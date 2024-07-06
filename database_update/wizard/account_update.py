from odoo import models, fields, api, _
from odoo.exceptions import UserError


class AccountDateUpdate(models.Model):
    _name = 'account.date.update'
    _description = 'Account Update Date'

    date = fields.Date('Update Date', required=True)

    def apply_update_date(self):
        selected_lines = self._context.get('active_ids')
        account_lines = self.env['account.move'].browse(selected_lines)

        for line in account_lines:
            line.write({
                'date': self.date,
            })


class AccountLineDateUpdate(models.Model):
    _name = 'account.line.date.update'
    _description = 'Account Line Update Date'

    date = fields.Date('Update Date', required=True)

    def apply_update_date(self):
        selected_lines = self._context.get('active_ids')
        account_move_lines = self.env['account.move.line'].browse(selected_lines)

        for line in account_move_lines:
            line.write({
                'date': self.date,
            })


class AccountMoveAccount(models.Model):
    _name = 'account.move.line.update'
    _description = 'Account Line Update Account'

    account_id = fields.Many2one('account.account', 'Update Account', required=True)

    def apply_update_account(self):
        selected_lines = self._context.get('active_ids')
        account_move_lines = self.env['account.move.line'].browse(selected_lines)

        for line in account_move_lines:
            line.write({
                'account_id': self.account_id.id,
            })

