from odoo import models, fields, api, _, tools


class StockQuant(models.Model):
    _inherit = 'stock.quant'

    standard_price = fields.Float(string='Unit Cost', related='product_id.standard_price')
    unit_value = fields.Float(string='Value', compute='_get_unit_value')

    def _get_unit_value(self):
        for quant in self:
            quant.unit_value = quant.standard_price * quant.inventory_quantity_auto_apply


class StockValuationLayer(models.Model):
    _inherit = 'stock.valuation.layer'

    standard_price = fields.Float('Unit Cost', related='product_id.standard_price')

    def init(self):
        tools.create_index(
            self._cr, 'stock_valuation_layer_index',
            self._table, ['product_id', 'remaining_qty', 'stock_move_id', 'analytic_account_id',
                          'company_id', 'create_date', 'date', 'standard_price']
        )


class StockAdjustmentLine(models.Model):
    _inherit = 'stock.adjustment.line'

    standard_price = fields.Float(string='Unit Cost',related='product_id.standard_price')
