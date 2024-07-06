import math
from odoo import api, models, fields


class PurchaseOrder(models.Model):

    _inherit = 'purchase.order'

    @api.onchange('order_line')
    def _calculate_purchase_foc(self):
        order_lines = self.order_line
        lines = [(2, l.id) for l in order_lines.filtered(lambda l: l.purchase_foc_id)]
        products = self.order_line.product_id
        purchase_foc_ids = self.env['purchase.foc'].search([('product_x_id', 'in', products.ids)])
        for purchase_foc_id in purchase_foc_ids:
            foc_order_lines = order_lines.filtered(lambda l: l.multi_uom_line_id == purchase_foc_id.product_x_multi_uom_line_id)
            qty = math.floor(sum(foc_order_lines.mapped('purchase_uom_qty')) / purchase_foc_id.product_x_qty) * purchase_foc_id.product_y_qty
            if qty <= 0:
                continue
            lines.append((0, 0, {
                'name': purchase_foc_id.name,
                'product_id': purchase_foc_id.product_y_id.id,
                'multi_uom_line_id': purchase_foc_id.product_y_multi_uom_line_id.id,
                'multi_price_unit': 0,
                'price_unit': 0,
                'purchase_uom_qty': qty,
                'product_uom': purchase_foc_id.product_y_id.uom_id.id,
                'product_qty': qty * purchase_foc_id.product_y_multi_uom_line_id.ratio,
                'taxes_id': False,
                'purchase_foc_id': purchase_foc_id.id,
                'date_planned': self.date_planned,
                'sequence': 1000,
            }))
        self.order_line = lines


class PurchaseOrderLine(models.Model):

    _inherit = 'purchase.order.line'

    purchase_foc_id = fields.Many2one('purchase.foc', 'Purchase FOC')

    def _prepare_account_move_line(self, move=False):
        values = super(PurchaseOrderLine, self)._prepare_account_move_line(move)
        values.update({
            'purchase_foc_id': self.purchase_foc_id,
        })
        return values

