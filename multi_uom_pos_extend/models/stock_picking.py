from odoo import api, models, fields
from itertools import groupby


class StockPicking(models.Model):

    _inherit = 'stock.picking'

    def _create_move_from_pos_order_lines(self, lines):
        self.ensure_one()
        lines_by_product = groupby(sorted(lines, key=lambda l: (l.product_id.id, l.multi_uom_line_id.id)), key=lambda l: (l.product_id.id, l.multi_uom_line_id.id))
        for (product_id, multi_uom_line_id), lines in lines_by_product:
            order_lines = self.env['pos.order.line'].concat(*lines)
            values = self._prepare_stock_move_vals(order_lines[0], order_lines)
            values['multi_uom_line_id'] = multi_uom_line_id
            current_move = self.env['stock.move'].create(values)
            confirmed_moves = current_move._action_confirm()
            confirmed_moves._add_mls_related_to_order(order_lines)
