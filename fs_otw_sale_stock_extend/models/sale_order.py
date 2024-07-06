from odoo import api, models, fields


class SaleOrder(models.Model):

    _inherit = 'sale.order'

    delivery_note = fields.Text('Delivery Note')

    def action_confirm(self):
        res = super().action_confirm()
        for order in self:
            order.picking_ids.write({
                'note': order.delivery_note,
                'payment_term_id': order.payment_term_id.id,
            })
        return res
