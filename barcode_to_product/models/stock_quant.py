from odoo import models, fields, api


class StockQuant(models.Model):
    _inherit = 'stock.quant'

    def open_product_form(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Product',
            'res_model': 'product.product',
            'view_type': 'form',
            'view_mode': 'form',
            'res_id': self.product_id.id,
            'target': 'current',
        }
