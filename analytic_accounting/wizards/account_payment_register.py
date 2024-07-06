from odoo import api, models, fields


class AccountPaymentRegister(models.TransientModel):

    _inherit = 'account.payment.register'

    analytic_account_id = fields.Many2one('account.analytic.account', 'Analytic Account')

    def _create_payment_vals_from_wizard(self):
        values = super(AccountPaymentRegister, self)._create_payment_vals_from_wizard()
        values['analytic_account_id'] = self.analytic_account_id.id
        return values

    def _create_payment_vals_from_batch(self, batch_result):
        values = super(AccountPaymentRegister, self)._create_payment_vals_from_batch(batch_result)
        values['analytic_account_id'] = batch_result['lines'].move_id.analytic_account_id.id
        return values
