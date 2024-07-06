from odoo import api, fields, models, tools, _


class ProductSequence(models.Model):
    _name = 'product.sequence'
    _description = 'Product Sequences'

    sequence = fields.Float('Sequence')
    product_group_id = fields.Many2one('product.group', 'Product Group')
    brand_id = fields.Many2one('product.brand', string="Brand Name")
