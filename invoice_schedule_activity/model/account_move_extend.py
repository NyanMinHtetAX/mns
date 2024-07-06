from odoo import models, fields, api, _
from odoo.fields import Date


class AccountMove(models.Model):
    _inherit = 'account.move'

    @api.model
    def run_activity_scheduler(self):
        today_date = Date.today()
        model_id = self.env['ir.model'].search([('model', '=', 'account.move')]).id
        mail_type_inv = self.env['mail.activity.type'].search([('name', '=', 'Call')]).id
        mail_type_bill = self.env['mail.activity.type'].search([('name', '=', 'To Do')]).id
        invoice_due_data = self.env['account.move'].search(
            [('invoice_date_due', '<', today_date), ('move_type', '=', 'out_invoice'),
             ('payment_state', '=', 'not_paid')])
        bill_bf_due_data = self.env['account.move'].search(
            [('invoice_date_due', '>', today_date), ('move_type', '=', 'in_invoice'),
             ('payment_state', '=', 'not_paid')])
        for rec in bill_bf_due_data:
            if not rec.activity_ids:
                rec.write({
                    'activity_ids': [
                        (0, 0, {
                            'activity_type_id':mail_type_bill,
                            'date_deadline': rec.invoice_date_due,
                            'summary': "PAID BEFORE DUE DATE",
                            'user_id': self.env.user.id,
                            'res_model_id': model_id,
                        })
                    ],
                })

        for rec in invoice_due_data:
            if not rec.activity_ids:
                rec.write({
                    'activity_ids': [
                        (0, 0, {
                            'activity_type_id': mail_type_inv,
                            'date_deadline': rec.invoice_date_due,
                            'summary': "DUE DATE IS OVER!",
                            'user_id': self.env.user.id,
                            'res_model_id': model_id,
                        })
                    ],
                })
