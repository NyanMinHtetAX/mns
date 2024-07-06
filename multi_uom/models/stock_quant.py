from odoo import api, models, fields


class StockQuant(models.Model):
    _inherit = 'stock.quant'

    multi_uom_onhand_qty = fields.Char('Multi UOM On Hand Qty', compute='convert_to_multi_uom')
    multi_uom_diff_qty = fields.Char('Multi UOM Diff Qty', compute='convert_diff_to_multi_uom')

    # Adding multi uom for Availability qty and difference qty between onhand and Availability qty
    m_uom_availability_qty = fields.Char('Multi UOM Availability Qty', compute='convert_to_multi_uom_availability')
    difference_qty = fields.Float('Difference Qty', default=0.0,store=True, compute='compute_difference_qty')

    @api.model
    def _get_inventory_fields_write(self):
        fields = super(StockQuant, self)._get_inventory_fields_write()
        return fields + ['multi_uom_onhand_qty', 'multi_uom_diff_qty', 'product_group_ids', 'm_uom_availability_qty']

    @api.depends('quantity')
    def convert_to_multi_uom(self):
        for rec in self:
            total_consumed_qty = 0
            multi_uom_qty = ''
            rec.multi_uom_onhand_qty = False
            product = rec.product_id
            qty = rec.quantity
            if product.multi_uom_ok and product.multi_uom_line_ids:
                lines = product.multi_uom_line_ids
                lines = sorted(lines, key=lambda l: l.ratio, reverse=True)
                remaining_qty = qty
                for line in lines:
                    if total_consumed_qty == qty:
                        break
                    converted_qty = remaining_qty / line.ratio
                    if abs(converted_qty) >= 1:
                        multi_uom_qty += f' {int(converted_qty)} {line.uom_id.name} '
                        consumed_qty = int(converted_qty) * line.ratio
                        remaining_qty -= consumed_qty
                        total_consumed_qty += consumed_qty
            else:
                multi_uom_qty = f'{qty} {product.uom_id.name}'
            rec.multi_uom_onhand_qty = multi_uom_qty

    @api.depends('inventory_diff_quantity')
    def convert_diff_to_multi_uom(self):
        for rec in self:
            total_consumed_qty = 0
            multi_uom_qty = ''
            product = rec.product_id
            qty = rec.inventory_diff_quantity
            if product.multi_uom_ok and product.multi_uom_line_ids:
                lines = product.multi_uom_line_ids
                lines = sorted(lines, key=lambda l: l.ratio, reverse=True)
                remaining_qty = qty
                for line in lines:
                    if total_consumed_qty == qty:
                        break
                    converted_qty = remaining_qty / line.ratio
                    if abs(converted_qty) >= 1:
                        multi_uom_qty += f' {int(converted_qty)} {line.uom_id.name} '
                        consumed_qty = int(converted_qty) * line.ratio
                        remaining_qty -= consumed_qty
                        total_consumed_qty += consumed_qty
            else:
                multi_uom_qty = f'{qty} {product.uom_id.name}'
            rec.multi_uom_diff_qty = multi_uom_qty

    @api.depends('available_quantity')
    def convert_to_multi_uom_availability(self):
        for rec in self:
            total_consumed_qty = 0
            multi_uom_qty = ''
            rec.multi_uom_onhand_qty = False
            product = rec.product_id
            qty = rec.available_quantity
            if product.multi_uom_ok and product.multi_uom_line_ids:
                lines = product.multi_uom_line_ids
                lines = sorted(lines, key=lambda l: l.ratio, reverse=True)
                remaining_qty = qty
                for line in lines:
                    if total_consumed_qty == qty:
                        break
                    converted_qty = remaining_qty / line.ratio
                    if abs(converted_qty) >= 1:
                        multi_uom_qty += f' {int(converted_qty)} {line.uom_id.name} '
                        consumed_qty = int(converted_qty) * line.ratio
                        remaining_qty -= consumed_qty
                        total_consumed_qty += consumed_qty
            else:
                multi_uom_qty = f'{qty} {product.uom_id.name}'
            rec.m_uom_availability_qty = multi_uom_qty

    @api.depends('available_quantity', 'quantity')
    def compute_difference_qty(self):
        for rec in self:
            rec.difference_qty = rec.quantity - rec.available_quantity
