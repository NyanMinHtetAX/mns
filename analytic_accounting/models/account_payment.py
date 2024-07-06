from odoo import api, models, fields


class AccountPayment(models.Model):

    _inherit = 'account.payment'

    analytic_account_id = fields.Many2one('account.analytic.account', 'Analytic Account')
    collector = fields.Char(string="Collector")
    branch = fields.Char(string="Branch")
    report_template_id = fields.Many2one('custom.report.template', string="Report Template", required=False)

    def update_analytic_account(self):
        for payment in self:
            payment.move_id.write({
                'analytic_account_id': payment.analytic_account_id.id,
            })
            payment.move_id.line_ids.write({
                'analytic_account_id': payment.analytic_account_id.id,
            })

    @api.model_create_multi
    def create(self, vals_list):
        payments = super(AccountPayment, self).create(vals_list)
        payments.update_analytic_account()
        return payments

    def action_post(self):
        res = super(AccountPayment, self).action_post()
        self.update_analytic_account()
        return res
