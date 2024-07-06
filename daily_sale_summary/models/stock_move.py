from odoo import api, models, fields


class StockMove(models.Model):

    _inherit = 'stock.move'

    van_order_line_id = fields.Many2one('van.order.line', 'Van Order Line')

    def _action_confirm(self, merge=True, merge_into=False):
        if self.picking_id.van_order_id:
            merge = False
        return super(StockMove, self)._action_confirm(merge, merge_into)
