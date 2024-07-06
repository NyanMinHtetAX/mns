from odoo import models, fields, api, _


class StockScrap(models.Model):
    _inherit = 'stock.scrap'

    reason = fields.Text(string='Scrap Reason')
    product_unit_cost = fields.Float(string='Unit Cost')

    @api.onchange('product_id')
    def onchange_product(self):
        for rec in self:
            if rec.product_id:
                rec.product_unit_cost = rec.product_id.standard_price
