from odoo import models, fields, api, _


class Order(models.Model):
    _name = 'jr.category'
    _description = 'Just Order Category'

    name = fields.Char(string='Category Name', required=True)
    parent_id = fields.Many2one('jr.category', string='Parent Category')
    child_id = fields.One2many('jr.category','parent_id', string='Child Category')
    image_128 = fields.Image("Image", max_width=128, max_height=128, store=True)
