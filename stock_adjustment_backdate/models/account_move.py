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
            today = fields.Date.today()
            user = self.env['res.users'].browse(self.env.context.get('uid'))
            invoice_allow_back_date = user.invoice_allow_back_date
            invoice_back_days = user.invoice_back_days or 0
            backdate_limit = today - relativedelta(days=invoice_back_days)
            if invoice_date < today and (not invoice_allow_back_date or invoice_date < backdate_limit):
                raise UserError(_('You are not allowed to do backdate transaction or your backdate is beyond limit (Invoice).'))
