from odoo import api, models, fields


class PurchaseFoc(models.Model):

    _name = 'purchase.foc'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Purchase FOC'

    name = fields.Char('Name')
    product_x_id = fields.Many2one('product.product', 'Product to Purchase')
    product_x_qty = fields.Float('Product to Purchase Qty')
    product_x_multi_uom_line_id = fields.Many2one('multi.uom.line', 'Product to Purchase UoM')
    product_x_tmpl_id = fields.Many2one('product.template', related='product_x_id.product_tmpl_id', string='Template Product to Purchase')
    product_y_id = fields.Many2one('product.product', 'FOC Product')
    product_y_qty = fields.Float('FOC Product Qty')
    product_y_multi_uom_line_id = fields.Many2one('multi.uom.line', 'FOC Product UoM')
    product_y_tmpl_id = fields.Many2one('product.template', related='product_y_id.product_tmpl_id', string='Template FOC Product')
    remarks = fields.Text('Remarks')
