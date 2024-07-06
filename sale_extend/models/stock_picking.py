from odoo import api, models, fields


class StockPicking(models.Model):

    _inherit = 'stock.picking'

    def _action_done(self):
        res = super(StockPicking, self)._action_done()
        for picking in self:
            if not picking.sale_id:
                continue
            order = picking.sale_id
            data_payload = {
                'model': 'sale.order',
                'order_id': order.id,
                'app_order_state': "Delivered",
            }
            order.partner_id.send_onesignal_notification('Order Delivered', 'Your order has been delivered.', data_payload)
        return res
