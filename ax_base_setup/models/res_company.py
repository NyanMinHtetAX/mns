from odoo import models, fields, api, tools, _, Command


class Company(models.Model):

    _inherit = "res.company"

    township_id = fields.Many2one('res.township',
                                  string='Township',
                                  compute='_compute_address',
                                  inverse='_set_city_code')
    city_code = fields.Char('City Code', compute='_compute_address', inverse='_set_township_id')
    is_foc = fields.Boolean('Sale FOC Item Discount')
    foc_discount_account_id = fields.Many2one('account.account', 'Sale FOC Item Discount Account')

    def _get_company_address_field_names(self):
        """ Return a list of fields coming from the address partner to match
        on company address fields. Fields are labeled same on both models. """
        return ['street', 'street2', 'city', 'zip', 'township_id', 'state_id', 'country_id']

    def _get_company_address_update(self, partner):
        return dict((fname, partner[fname]) for fname in self._get_company_address_field_names())

    def _compute_address(self):
        for company in self.filtered(lambda company: company.partner_id):
            address_data = company.partner_id.sudo().address_get(adr_pref=['contact'])
            if address_data['contact']:
                partner = company.partner_id.browse(address_data['contact']).sudo()
                company.update(company._get_company_address_update(partner))

    def _set_city_code(self):
        for company in self:
            company.partner_id.city_code = company.city_code

    def _set_township_id(self):
        for company in self:
            company.partner_id.township_id = company.township_id

    @api.onchange('township_id')
    def onchange_township(self):
        self.zip = self.township_id.zip
        self.city = self.township_id.city_id.name
        self.city_code = self.township_id.city_id.code
        self.state_id = self.township_id.state_id
        self.country_id = self.township_id.country_id

    @api.model
    def create(self, vals):
        if not vals.get('favicon'):
            vals['favicon'] = self._get_default_favicon()
        if not vals.get('name') or vals.get('partner_id'):
            self.clear_caches()
            return super(Company, self).create(vals)
        partner = self.env['res.partner'].create({
            'name': vals['name'],
            'is_company': True,
            'image_1920': vals.get('logo'),
            'email': vals.get('email'),
            'phone': vals.get('phone'),
            'website': vals.get('website'),
            'vat': vals.get('vat'),
            'country_id': vals.get('country_id'),
            'township_id': vals.get('township_id'),
            'city_code': vals.get('city_code'),
        })

        # compute stored fields, for example address dependent fields
        partner.flush()
        vals['partner_id'] = partner.id
        self.clear_caches()
        company = super(Company, self).create(vals)
        # The write is made on the user to set it automatically in the multi company group.
        self.env.user.write({'company_ids': [Command.link(company.id)]})

        # Make sure that the selected currency is enabled
        if vals.get('currency_id'):
            currency = self.env['res.currency'].browse(vals['currency_id'])
            if not currency.active:
                currency.write({'active': True})
        return company
