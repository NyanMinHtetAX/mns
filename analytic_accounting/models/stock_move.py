from odoo import api, models, fields


class StockMove(models.Model):

    _inherit = 'stock.move'

    analytic_account_id = fields.Many2one('account.analytic.account', 'Analytic Account')

    def _action_done(self, cancel_backorder=False):
        res = super(StockMove, self)._action_done(cancel_backorder=cancel_backorder)
        for move in self:
            move.move_line_ids.write({'analytic_account_id': move.analytic_account_id.id})
        return res

    def _prepare_account_move_vals(self, credit_account_id, debit_account_id, journal_id, qty, description, svl_id, cost):
        values = super(StockMove, self)._prepare_account_move_vals(credit_account_id,
                                                                   debit_account_id,
                                                                   journal_id,
                                                                   qty,
                                                                   description,
                                                                   svl_id,
                                                                   cost)
        self.env['stock.valuation.layer'].browse(svl_id).write({'analytic_account_id': self.analytic_account_id.id})
        values['analytic_account_id'] = self.analytic_account_id.id
        return values

    def _generate_valuation_lines_data(self, partner_id, qty, debit_value, credit_value, debit_account_id, credit_account_id, description):
        lines = super(StockMove, self)._generate_valuation_lines_data(partner_id,
                                                                      qty,
                                                                      debit_value,
                                                                      credit_value,
                                                                      debit_account_id,
                                                                      credit_account_id,
                                                                      description)
        for key in lines.keys():
            lines[key]['analytic_account_id'] = self.analytic_account_id.id
        return lines

    def _create_in_svl(self, forced_quantity=None):
        svls = super(StockMove, self)._create_in_svl(forced_quantity)
        svls.write({'analytic_account_id': self.analytic_account_id.id})
        return svls

    def _create_out_svl(self, forced_quantity=None):
        svls = super(StockMove, self)._create_out_svl(forced_quantity)
        svls.write({'analytic_account_id': self.analytic_account_id.id})
        return svls


class StockMoveLine(models.Model):

    _inherit = 'stock.move.line'

    analytic_account_id = fields.Many2one('account.analytic.account', 'Analytic Account')
