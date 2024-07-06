from odoo import api, models, fields


class AccountBankStatement(models.Model):

    _inherit = 'account.bank.statement'

    analytic_account_id = fields.Many2one('account.analytic.account', 'Analytic Account')

    def button_post(self):
        res = super(AccountBankStatement, self).button_post()
        for statement in self:
            statement._update_analytic_account()
        return res

    def _update_analytic_account(self):
        analytic_account_id = self.analytic_account_id.id
        self.line_ids.write({'analytic_account_id': analytic_account_id})
        self.move_line_ids.write({'analytic_account_id': analytic_account_id})
        self.move_line_ids.move_id.write({'analytic_account_id': analytic_account_id})


class AccountBankStatementLine(models.Model):

    _inherit = 'account.bank.statement.line'

    analytic_account_id = fields.Many2one('account.analytic.account', 'Analytic Account')
