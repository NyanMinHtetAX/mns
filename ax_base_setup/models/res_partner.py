from odoo import api, fields, models, tools, _
from odoo import exceptions
from odoo.exceptions import ValidationError

ADDRESS_FIELDS = ['street', 'street2', 'zip', 'city', 'state_id', 'country_id', 'township_id']


class Partner(models.Model):

    _inherit = "res.partner"

    township_id = fields.Many2one('res.township',
                                  string='Township',
                                  ondelete='restrict',
                                  domain="[('city_id', '=?', x_city_id)]")
    city = fields.Char(related='x_city_id.name', string='City Char')
    city_code = fields.Char('City Code')
    x_city_id = fields.Many2one('res.city',
                                string='City',
                                domain="[('state_id', '=?', state_id)]",
                                ondelete='restrict')
    company_register_id = fields.Char(string='Company Register ID')
    viber_no = fields.Char(string='Viber')
    what_app_no = fields.Char(string='Whatsapp')
    we_chat = fields.Char(string='WeChat')
    facebook_link = fields.Char(string='Facebook Link')
    date_of_birth = fields.Date(string='Date Of Birth')
    religion_id = fields.Many2one('res.religion', string='Religion')
    customer = fields.Boolean(string='Is a Customer?',
                              help="Check this box if this contact is a customer. It can be selected in sales orders.")
    supplier = fields.Boolean(string='Is a Vendor',
                              help="Check this box if this contact is a vendor. It can be selected in purchase orders.")
    over_credit = fields.Boolean('Disallow Over Credit?')
    credit_limit = fields.Float('Credit Limit Amount')
    over_payment = fields.Boolean(string="Unallow Payment?")

    v_over_credit = fields.Boolean('Vendor Disallow Over Credit?')
    v_credit_limit = fields.Float('Vendor Credit Limit Amount')
    v_over_payment = fields.Boolean(string="Vendor Unallow Payment?")

    amount_due = fields.Monetary('Due Amount', compute='_compute_amount_due')
    ref = fields.Char(string='Reference', index=True, copy=False)


    @api.constrains('name')
    def check_contact_name(self):
        for rec in self:
            supplier_name = self.env['res.partner'].search([('name', '=', rec.name),
                                                            ('supplier', '=', True),
                                                            ('id', '!=', rec.id)])
            customer_name = self.env['res.partner'].search([('name', '=', rec.name),
                                                            ('customer', '=', True),
                                                            ('id', '!=', rec.id)])
            if supplier_name:
                raise ValidationError(_("Supplier(%s) already exists." % rec.name))
            elif customer_name:
                raise ValidationError(_("Customer(%s) already exists." % rec.name))
            else:
                pass

    @api.constrains('ref')
    def check_ref(self):
        for record in self:
            if record.ref:
                ref = self.env['res.partner'].search([('ref', '=', record.ref), ('id', '!=', record.id)])
                if ref:
                    raise ValidationError("Reference(%s) already exists." % record.ref)


    @api.depends('credit', 'debit')
    def _compute_amount_due(self):
        for rec in self:
            rec.amount_due = rec.credit - rec.debit

    @api.model
    def default_get(self, fields_list):
        values = super(Partner, self).default_get(fields_list)
        values['country_id'] = self.env.company.country_id.id
        return values

    @api.onchange('state_id')
    def _onchange_states_id(self):
        if self.state_id and self.state_id != self.x_city_id.state_id:
            self.x_city_id = False
        if self.state_id and self.state_id != self.township_id.state_id:
            self.township_id = False

    @api.onchange('x_city_id')
    def _onchange_city_id(self):
        if self.x_city_id and self.x_city_id != self.township_id.city_id:
            self.township_id = False
        if self.x_city_id:
            self.city_code = self.x_city_id.code
        else:
            self.city_code = False

    @api.onchange('township_id')
    def onchange_township(self):
        if self.township_id:
            self.zip = self.township_id.zip
            self.x_city_id = self.township_id.city_id
            self.city_code = self.township_id.city_code
            self.city = self.township_id.city_id
            self.state_id = self.township_id.state_id
            self.country_id = self.township_id.country_id

    @api.model
    def _address_fields(self):
        """Returns the list of address fields that are synced from the parent."""
        return ADDRESS_FIELDS

    @api.model
    def _formatting_address_fields(self):
        """Returns the list of address fields usable to format addresses."""
        return self._address_fields()

    def update_address(self, vals):
        addr_vals = {key: vals[key] for key in self._address_fields() if key in vals}
        if addr_vals:
            return super(Partner, self).write(addr_vals)

    @api.model
    def _get_default_address_format(self):
        return "%(street)s\n%(street2)s\n%(township_name)s %(city)s\n%(state_name)s %(country_name)s"

    @api.model
    def _get_address_format(self):
        return self.country_id.address_format or self._get_default_address_format()

    def _prepare_display_address(self, without_company=False):
        '''
        The purpose of this function is to build and return an address formatted accordingly to the
        standards of the country where it belongs.

        :param address: browse record of the res.partner to format
        :returns: the address formatted in a display that fit its country habits (or the default ones
            if not country is specified)
        :rtype: string
        '''
        # get the information that will be injected into the display format
        # get the address format
        address_format = self._get_address_format()
        args = {
            'township_name': self.township_id.name or '',
            'township_code': self.township_id.code or '',
            'city_name': self.x_city_id.name or '',
            'city_code': self.x_city_id.code or '',
            'state_code': self.state_id.code or '',
            'state_name': self.state_id.name or '',
            'country_code': self.country_id.code or '',
            'country_name': self._get_country_name(),
            'company_name': self.commercial_company_name or '',
        }
        for field in self._formatting_address_fields():
            args[field] = getattr(self, field) or ''
        if without_company:
            args['company_name'] = ''
        elif self.commercial_company_name:
            address_format = '%(company_name)s\n' + address_format
        return address_format, args

    def _display_address_depends(self):
        # field dependencies of method _display_address()
        return self._formatting_address_fields() + [
            'country_id.address_format', 'country_id.code', 'country_id.name', 'x_city_id.name', 'x_city_id.code',
            'company_name', 'state_id.code', 'state_id.name', 'township_id.name', 'township_id.code'
        ]

    def generate_sequence_code(self):
        for partner in self:
            if partner.customer or partner.supplier:
                if partner.customer:
                    sequence_id = partner.state_id.customer_sequence_id
                else:
                    sequence_id = partner.state_id.supplier_sequence_id
                if sequence_id:
                    partner.ref = sequence_id.next_by_id()
                else:
                    raise exceptions.ValidationError(f'Sequence is missing for some partner\'s state.')



