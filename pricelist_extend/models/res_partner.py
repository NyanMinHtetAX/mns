from odoo import api, models, fields


class Partner(models.Model):

    _inherit = 'res.partner'

    pricelist_ids = fields.Many2many('product.pricelist', string='Allow Pricelist')