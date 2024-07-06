from odoo import api, models, fields


class StockValuationLayer(models.Model):

    _inherit = 'stock.valuation.layer'

    analytic_account_id = fields.Many2one('account.analytic.account', 'Analytic Account')

