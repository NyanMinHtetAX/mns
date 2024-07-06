from odoo import api, models, fields, _
from odoo.exceptions import UserError
from datetime import datetime
from dateutil.relativedelta import relativedelta

class AccountMove(models.Model):

    _inherit = 'account.move'

    @api.constrains('invoice_date')
    def check_date_order(self):
        for account_move in self:
            invoice_date = account_move.invoice_date
            if not invoice_date:
                continue
            user = self.env.user
            invoice_allow_lock_date = user.invoice_allow_lock_date
            invoice_lock_date = user.invoice_lock_date or ''
            if invoice_allow_lock_date and invoice_date <= invoice_lock_date:
                raise UserError(_('You are not allowed because your order date is beyond lock date limit.'))
            else:
                continue

    def write(self, vals):
        res = super(AccountMove, self).write(vals)
        for account_move in self:
            invoice_date = account_move.invoice_date
            if not invoice_date:
                continue
            user = self.env.user
            invoice_allow_lock_date = user.invoice_allow_lock_date
            invoice_lock_date = user.invoice_lock_date or ''
            if invoice_allow_lock_date and invoice_date <= invoice_lock_date:
                raise UserError(_('You are not allowed because your order date is beyond lock date limit.'))
            else:
                continue
        return res
