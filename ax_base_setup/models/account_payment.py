from odoo import api, fields, models, _


class AccountPayment(models.Model):

    _inherit = "account.payment"

    country_code = fields.Char(string='Country-Code')
    due_date = fields.Date('Today Date', required=True, readonly=False, default=fields.date.today())

    @api.onchange('payment_type')
    def onchange_payment_type_domain(self):
        type = self.payment_type
        if type == 'inbound':
            return {'domain': {'partner_id': [('customer', '=', True)]}}
        elif type == 'outbound':
            return {'domain': {'partner_id': [('supplier', '=', True)]}}

