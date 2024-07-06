from odoo import api, models, fields, _


class ProductGroup(models.Model):

    _name = 'product.group'
    _description = 'Product Group'


    _sql_constraints = [
        ('unique_code', 'unique(code)', 'The code of the product group must be unique !'),
        ('name_uniq', 'unique (name)', 'The name of the product group must be unique !'),
    ]

    name = fields.Char('Name', required=1)
    description = fields.Text('Description')
    code = fields.Char(string='Code')


class ProductTemplate(models.Model):

    _inherit = 'product.template'

    product_group_id = fields.Many2one('product.group', 'Product Group')


class ProductProduct(models.Model):

    _inherit = 'product.product'

    product_group_id = fields.Many2one('product.group',
                                       string='Product Group',
                                       related='product_tmpl_id.product_group_id',
                                       store=True)
