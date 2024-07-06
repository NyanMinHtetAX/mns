from odoo import models, fields, api, _


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    sale_type =fields.Selection([('normal', 'Sale'),
                                ('pre_order', 'Pre Order')], 'Type', default='normal')

    @api.onchange('sale_type')
    def onchange_sale_type(self):
        if self.sale_type == 'normal':
            return {'domain': {'team_id': [('is_van_team', '=', False)]}}
        else:
            return {'domain': {'team_id': [('is_van_team', '=', True)]}}