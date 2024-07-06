from odoo import models, fields, api, _


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    final_sale_price = fields.Float(string='Final Sale Price')
