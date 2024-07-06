from odoo import models, fields, api, _


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    sale_team = fields.Many2one('crm.team', string='Sale Team')
    fs_description = fields.Text('Van Description')
