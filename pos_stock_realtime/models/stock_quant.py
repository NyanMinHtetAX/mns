from odoo import api, fields, models
from collections import deque


class StockQuant(models.Model):
    _inherit = 'stock.quant'

    @api.model
    def get_qty_available(self, picking_type_id, location_ids=None, product_ids=None):
        if picking_type_id:
            domain = [('id', '=', picking_type_id)]
            picking_type = self.env['stock.picking.type'].search(domain, limit=1)
            location_id = picking_type and picking_type.default_location_src_id.id
            domain = [
                ('usage', '=', 'internal'),
                ('id', 'child_of', location_id)
            ]
            all_locations = self.env['stock.location'].search(domain)

            stock_quant = self.search_read(
                [('location_id', 'in', all_locations.ids)],
                ['product_id', 'quantity', 'location_id'])
            print(stock_quant, 'sssssssssssssssssssssssss')
            return stock_quant

        else:
            stock_quant = self.search_read(
                [('location_id', 'in', location_ids),
                 ('product_id', 'in', product_ids)],

                ['product_id', 'quantity', 'location_id'])
            print('ssssssssssssssaaaaaaaaaaaaaaaaaaaa',stock_quant)
            return stock_quant
