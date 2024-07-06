from odoo import models, fields, api, _


class Wishlist(models.Model):
    _name = 'jr.wishlist'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Wishlist'

    date = fields.Date(string='Date', default=fields.Date.today)
    categ_id = fields.Many2one('product.category',related='product_id.categ_id',string='Product Category' , store=True)
    product_id = fields.Many2one('product.product', string='Product')
    customer_id = fields.Many2one('res.partner', string='Customer')
    company_id = fields.Many2one('res.company')
