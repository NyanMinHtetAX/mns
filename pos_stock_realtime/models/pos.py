from odoo import api, models, fields, _

class ProductProduct(models.Model):
    _inherit = 'product.product'

    onhand_qty = fields.Integer(string='Onhand Qty')
    is_check = fields.Boolean(string='Check?')

class PosConfig(models.Model):

    _inherit = 'pos.config'

    show_qty_available = fields.Boolean('Display Stock in POS', help="Apply show quantity of POS", default=True)
    location_only = fields.Boolean('Count only for POS Location', help='Only Show Stock Qty in this POS Location')
    allow_out_of_stock = fields.Boolean('Allow Out-of-Stock')
    limit_qty = fields.Integer('Deny Order When Available Qty Is Lower Than')
    hide_product = fields.Boolean('Hide Products which are not in POS Location',
                                  help='Hide products with negative stocks or not exist in the stock location of this POS')
    stock_location_id = fields.Many2one('stock.location', 'Stock Location', related='picking_type_id.default_location_src_id', store=True)

class PosOrder(models.Model):
    _inherit = 'pos.order'

    @api.model
    def check_on_hand_qty(self, order, config_id):
        insufficient_products = []
        config = self.env['pos.config'].browse(config_id)
        location = config.picking_type_id.default_location_src_id
        order_lines = order['lines']
        for order_line in order_lines:
            values = order_line[2]
            product = self.env['product.product'].browse(values['product_id'])
            if product.detailed_type != 'product':
                continue
            qty = values['qty']
            if qty < 0:
                continue
            if values.get('multi_uom_line_id', False):
                multi_uom_line = self.env['multi.uom.line'].browse(values['multi_uom_line_id'])
                qty = multi_uom_line.ratio * qty
            else:
                qty = values['qty']
            quants = self.env['stock.quant'].search([('product_id', '=', product.id),
                                                     ('location_id', '=', location.id)])
            on_hand_qty = sum(quants.mapped('quantity'))
            if on_hand_qty < qty:
                insufficient_products.append(product)
                print(on_hand_qty,qty,'//////////////////////////////')
        if insufficient_products:
            error_message = f'Some products are not sufficient in the inventory. They are \n' \
                            f'{", ".join([p.name for p in insufficient_products])}'
        else:
            error_message = False

        return error_message

    @api.model
    def check_on_hand_qty1(self, product_id, config_id):
        config = self.env['pos.config'].browse(config_id)
        location = config.picking_type_id.default_location_src_id
        product = self.env['product.product'].browse(product_id)
        quants = self.env['stock.quant'].search([('product_id', '=', product.id),
                                                 ('location_id', '=', location.id)])
        on_hand_qty = sum(quants.mapped('quantity'))

        return on_hand_qty

