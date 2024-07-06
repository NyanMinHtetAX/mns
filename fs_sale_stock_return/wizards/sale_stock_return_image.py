from odoo import api, models, fields


class SaleStockReturnImage(models.Model):

    _name = 'sale.stock.return.image'
    _description = 'Sale Stock Return Image'

    name = fields.Char('Description')
    image = fields.Image('Image')
    sale_stock_return_id = fields.Many2one('sale.stock.return', 'Sale Stock Return')
