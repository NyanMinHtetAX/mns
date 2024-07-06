from odoo import api, models, fields


class StockMove(models.Model):

    _inherit = 'stock.move'

    sale_stock_return_id = fields.Many2one('sale.stock.return', 'Sale Stock Return')
    sale_stock_return_line_id = fields.Many2one('sale.stock.return.line', 'Sale Stock Return Line')
