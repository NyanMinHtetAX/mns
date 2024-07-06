from odoo import api, models, fields


class AccountMove(models.Model):

    _inherit = 'account.move'

    analytic_account_id = fields.Many2one('account.analytic.account', 'Analytic Account')

    @api.onchange('analytic_account_id', 'line_ids')
    def onchange_analytic_account_id(self):
        self.line_ids.update({
            'analytic_account_id': self.analytic_account_id.id,
        })

    def _reverse_move_vals(self, default_values, cancel=True):

        move_values = super(AccountMove, self)._reverse_move_vals(default_values, cancel)

        analytic_account_id = move_values['analytic_account_id']
        for line in move_values['line_ids']:
            line[2]['analytic_account_id'] = analytic_account_id
        return move_values

    def _post(self, soft=True):
        res = super(AccountMove, self)._post(soft=soft)
        for move in self:
            move.line_ids.write({'analytic_account_id': move.analytic_account_id.id})
        return res
