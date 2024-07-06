from odoo import models, fields, api, _


class Order(models.Model):
    _name = 'jr.order'
    _description = 'Just Order Order'
    order_name = fields.Char(string='Order Name')


