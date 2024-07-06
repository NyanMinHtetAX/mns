from odoo import models, fields, api, _


class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    city_id = fields.Many2one('res.city', string='Cities', related='partner_id.x_city_id', store=True)
    picking_type_id = fields.Many2one('stock.picking.type', string='Deliver To', related='order_id.picking_type_id',
                                      store=True)
    warehouse_id = fields.Many2one('stock.warehouse', string='Warehouse', related='picking_type_id.warehouse_id',
                                   store=True)
    purchase_return_qty = fields.Float(string='Return Qty', compute='get_return_qty',store=True)
    # purchase_backorder_qty = fields.Float(string='Backorder Qty', compute='get_backorder_qty', store=True)
    backorder_qty = fields.Float(string='Backorder Quantity', compute='_compute_backorder_qty', store=True)

    date_order = fields.Datetime('Order Date', readonly=True,store=True)
    state = fields.Selection([
                                ('draft', 'Draft RFQ'),
                                ('sent', 'RFQ Sent'),
                                ('to approve', 'To Approve'),
                                ('purchase', 'Purchase Order'),
                                ('done', 'Done'),
                                ('cancel', 'Cancelled')
                            ], 'Status', readonly=True)

    # @api.depends('order_id.picking_ids')
    # def get_backorder_qty(self):
    #     for line in self:
    #         backorder_qty = 0.0
    #         for picking in line.order_id.picking_ids:
    #             if picking.state == 'assigned':
    #                 for move in picking.move_lines:
    #                     if move.purchase_line_id == line:
    #                          if line.multi_qty_received > 0:
    #                             backorder_qty += move.multi_uom_qty - move.multi_quantity_done
    #                          else:
    #                             line.purchase_backorder_qty = 0
    #         line.purchase_backorder_qty = backorder_qty


    @api.depends('move_ids.picking_id.backorder_id.state','purchase_uom_qty', 'multi_qty_received', 'move_ids.picking_id.backorder_id')
    def _compute_backorder_qty(self):
        for line in self:
            backorder_qty = 0
            for move in line.move_ids:
                if line.purchase_uom_qty == line.multi_qty_received:
                    line.backorder_qty = 0
                else:
                  if move.picking_id.backorder_id and move.picking_id.state == 'assigned':
                     backorder_qty += move.multi_uom_qty - move.multi_quantity_done
            line.backorder_qty = backorder_qty




    @api.depends('purchase_uom_qty', 'multi_qty_received')
    def get_return_qty(self):
        self.purchase_return_qty = 0
        for line in self:
            move_ids = self.env['stock.move'].search([
                ('purchase_line_id', '=', line.id),
                ('state', '=', 'done'),
                ('to_refund', '=', True),
            ])
            if move_ids:
                supplier_location_ids = self.env['stock.warehouse'].search(
                    [('partner_id', '=', line.order_id.partner_id.id)]).mapped(
                    'lot_stock_id').location_id.child_ids.filtered(lambda l: l.usage == 'supplier').ids
                return_move_ids = move_ids.filtered(lambda m: m.location_id.id not in supplier_location_ids)
                return_to_vendor_qty = sum(
                    return_move_ids.filtered(lambda l: l.location_id.usage == 'internal').mapped('multi_uom_qty'))
                return_from_vendor_qty = sum(
                    return_move_ids.filtered(lambda l: l.location_id.usage == 'supplier').mapped('multi_uom_qty'))
                line.purchase_return_qty = return_to_vendor_qty - return_from_vendor_qty

    def _group_by_sale(self, groupby=''):
        res = super()._group_by_purchase(groupby)
        res += """,po.date_order as date_order,po.sate as state, """
        return res

    def _select_additional_fields(self, fields):
        fields['date_order'] = ", po.date_order as date_order"
        fields['state'] = ", po.sate as state"
        return super()._select_additional_fields(fields)
