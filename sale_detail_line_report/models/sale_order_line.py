from odoo import api, models, fields


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    city_id = fields.Many2one('res.city', string='Cities', related='order_partner_id.x_city_id', store=True)
    warehouse_id = fields.Many2one('stock.warehouse', string='Warehouse', related='order_id.warehouse_id', store=True)

    sale_return_qty = fields.Float(string='Return Qty', compute='get_return_qty', store=True)
    team_id = fields.Many2one('crm.team', string='Sale Team', related='order_id.team_id', readonly=True, store=True)

    @api.depends('multi_uom_qty', 'multi_qty_delivered')
    def get_return_qty(self):
        self.sale_return_qty = 0
        for i in self.order_id:
            picking_ids = self.env['stock.picking'].search([('sale_id', '=', i.id)])
            move_ids = self.env['stock.move'].search([('picking_id', 'in', picking_ids.ids)])
            check_return = move_ids.filtered(lambda l: l.to_refund == True)
            if check_return:
                return_from_customer = check_return.filtered(lambda l: l.location_id.usage == 'customer')
                return_to_customer = check_return.filtered(lambda l: l.location_id.usage == 'internal')
                for rec in self:
                    return_from_qty = sum(return_from_customer.filtered(
                        lambda l: l.state == 'done' and l.product_id == rec.product_id).mapped('multi_uom_qty'))
                    return_to_qty = sum(return_to_customer.filtered(
                        lambda l: l.state == 'done' and l.product_id == rec.product_id).mapped('multi_uom_qty'))
                    rec.sale_return_qty = return_from_qty - return_to_qty
