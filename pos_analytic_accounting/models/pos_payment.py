from odoo import api, models, fields


class PosPayment(models.Model):

    _inherit = 'pos.payment'

    analytic_account_id = fields.Many2one('account.analytic.account', 'Analytic Account')

    @api.model
    def create(self, values):
        order = self.env['pos.order'].browse(values.get('pos_order_id', False))
        values['analytic_account_id'] = order.session_id.config_id.analytic_account_id.id
        return super(PosPayment, self).create(values)
