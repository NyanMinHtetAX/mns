from odoo import fields, models, api
from odoo.exceptions import UserError, ValidationError

class ResConfigSettings(models.Model):
    _name = 'jr.config'
    _description = 'For Just Order Setting'
    _rec_name = 'app_name'

    app_name = fields.Char(string='App Name')
    color = fields.Char(string="Color Picker")
    product_mcom_image_ids = fields.One2many('product.jr.images', 'jr_config_id', string="Extra Product Media", limit=4,
                                             copy=True)
    def _default_pricelist(self):
        return self.env['product.pricelist'].search([('company_id', 'in', (False, self.env.company.id)), ('currency_id', '=', self.env.company.currency_id.id)], limit=1)

    shop_name = fields.Char(string='Shop Name')
    address = fields.Char(string='Address')
    phone = fields.Char(string='Phone')
    description = fields.Text(string='Description',)
    pricelist_id = fields.Many2one('product.pricelist', string='Default Pricelist', required=True,
                                   default=_default_pricelist,
                                   help="The pricelist used if no customer is selected or if the customer has no Sale Pricelist configured.")
    property_payment_term_id = fields.Many2one('account.payment.term', string='Payment Terms')
    working_hour = fields.Char(string='Working Hour')
    ph_no = fields.Char(string='Phone No')
    remark = fields.Char(string='Remark')
    image_1920 = fields.Binary()
    key = fields.Char('')
    company_id = fields.Many2one('res.company')
    term_and_condition = fields.Html('Terms and conditions', translate=True)

    @api.constrains('company_id')
    def _check_company(self):
        for rec in self:
            config_data = self.env['jr.config'].sudo().search([('id','!=',self.id),('company_id','=',rec.company_id.id)])
            if config_data:
                raise UserError(rec.company_id.name + " is already existed in other settings")

    @api.onchange('phone','ph_no')
    def _onchange_phone(self):
        if self.phone and not self.phone.startswith('+'):
            self.phone = '+959 ' + self.phone
        if self.ph_no and not self.ph_no.startswith('+'):
            self.ph_no = '+959 ' + self.ph_no

    def _get_default_access_token(self):
        categ1 = {
            'access_key': 'map.api.key',
            'access_value': ''
        }
        categ2 = {
            'access_key': 'sms.api.key',
            'access_value': ''
        }
        categ3 = {
            'access_key': 'map.app.id',
            'access_value': ''
        }

        return [(0, 0, categ1), (0, 0, categ2), (0, 0, categ3)]

    access_token_ids = fields.One2many('access.token', 'access_token_id', string='Access Token',
                                       default=_get_default_access_token)


class AccessToken(models.Model):
    _name = 'access.token'
    description = 'Access Token'

    access_key = fields.Char(string='Key')
    access_value = fields.Char(string='Values')

    access_token_id = fields.Many2one('jr.config', string='Access Token')
