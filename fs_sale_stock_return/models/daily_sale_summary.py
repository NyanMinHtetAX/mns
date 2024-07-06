from odoo import api, fields, models, _
from odoo.exceptions import UserError


class DailySale(models.Model):

    _inherit = "daily.sale.summary"

    return_payment_count = fields.Integer(compute='_compute_return_payment_count', string='Return Payment Count')

    return_payment_ids = fields.One2many('sale.return.payment', 'daily_sale_summary_id', 'Return Payments')
    
    def action_view_return_payments(self):
        treeview_ref = self.env.ref('fs_sale_stock_return.view_return_payment_tree', False)

        return {
            'name': 'Return Payments',
            'type': 'ir.actions.act_window',
            'res_model': 'sale.return.payment',
            'view_mode': 'tree,form',
            'view_id': False,
            'domain': [('id', 'in', self.return_payment_ids.ids)]
        }

    def _compute_return_payment_count(self):
        for record in self:
            record.return_payment_count = len(record.return_payment_ids)