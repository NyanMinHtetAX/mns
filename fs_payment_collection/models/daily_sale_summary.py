from odoo import api, fields, models, _
from odoo.exceptions import UserError


class DailySale(models.Model):

    _inherit = "daily.sale.summary"

    payment_payment_ids = fields.One2many('payment.collection.one.payment.line', 'daily_sale_summary_id', 'Advanced Payments')
    cash_payment_ids = fields.One2many('payment.collection.payment.line', 'daily_sale_summary_id', 'Cash Collection Payments')
    cash_payment_count = fields.Integer(compute='_compute_cash_collect_payment_count', string='Cash Collection Payment Count')
    payment_payment_count = fields.Integer(compute='_compute_payment_collect_payment_count', string="Payment Collection Payment Count")
    
    def action_view_cash_payments(self):

        return {
            'name': 'Cash Collection Payments',
            'type': 'ir.actions.act_window',
            'res_model': 'payment.collection.payment.line',
            'view_mode': 'tree,form',
            'view_id': False,
            'domain': [('id', 'in', self.cash_payment_ids.ids)]
        }


    def action_view_payment_payments(self):

        return {
            'name': 'Payment Collection Payments',
            'type': 'ir.actions.act_window',
            'res_model': 'payment.collection.one.payment.line',
            'view_mode': 'tree,form',
            'view_id': False,
            'domain': [('id', 'in', self.payment_payment_ids.ids)]
        }

    def _compute_cash_collect_payment_count(self):
        for record in self:
            record.cash_payment_count = len(record.cash_payment_ids)

    def _compute_payment_collect_payment_count(self):
        for record in self:
            record.payment_payment_count = len(record.payment_payment_ids)