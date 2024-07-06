from odoo import api, models, fields


class PosSession(models.Model):

    _inherit = 'pos.session'

    analytic_account_id = fields.Many2one('account.analytic.account', 'Analytic Account')

    @api.model
    def create(self, values):
        config_id = values.get('config_id', False) or self.env.context.get('default_config_id', False)
        analytic_account_id = self.env['pos.config'].sudo().browse(config_id).analytic_account_id.id
        values['analytic_account_id'] = analytic_account_id
        res = super(PosSession, self).create(values)
        res.statement_ids.write({'analytic_account_id': analytic_account_id})
        return res

    def _prepare_line(self, order_line):
        values = super(PosSession, self)._prepare_line(order_line)
        values['analytic_account_id'] = order_line.order_id.analytic_account_id.id
        return values

    def _validate_session(self, balancing_account=False, amount_to_balance=0, bank_payment_method_diffs=None):
        res = super(PosSession, self)._validate_session(balancing_account, amount_to_balance, bank_payment_method_diffs)
        moves = self._get_related_account_moves()
        moves.write({'analytic_account_id': self.analytic_account_id.id})
        moves.line_ids.write({'analytic_account_id': self.analytic_account_id.id})
        return res
