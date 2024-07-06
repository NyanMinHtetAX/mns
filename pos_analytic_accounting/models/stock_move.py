from odoo import api, models, fields


class StockMove(models.Model):

    _inherit = 'stock.move'

    def _prepare_move_line_vals(self, quantity=None, reserved_quant=None):
        values = super(StockMove, self)._prepare_move_line_vals(quantity, reserved_quant)
        values['analytic_account_id'] = self.analytic_account_id.id
        return values

