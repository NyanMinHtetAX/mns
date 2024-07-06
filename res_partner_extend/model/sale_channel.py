from odoo import api, models, fields, _


class SaleChannel(models.Model):

    _name = 'res.sale.channel'
    _description = 'Sale Channel'

    name = fields.Char('Name', required=1)
