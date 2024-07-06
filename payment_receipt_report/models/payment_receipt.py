import datetime

from dateutil.relativedelta import relativedelta
from odoo import api, models, fields

class PaymentReceipt(models.Model):
    _inherit = 'account.payment'

    def get_cash_receipt(self):
        records = []
        lines = []
        print_date = datetime.datetime.now() + relativedelta(hours=6.5)

        for order in self:
            report_template_id = []
            if order.report_template_id:
                for temp in order.report_template_id:
                    report_template_id.append({
                        'title_img': temp.image_1920 or '',
                        'title1': temp.title1 or '',
                        'title2': temp.title2 or '',
                        'address': temp.address or '',
                        'company_phone': temp.company_phone or '',
                        'social_viber': temp.social_viber or '',
                        'social_mail': temp.social_mail or '',
                        'thank': temp.thank or '',
                        'complain': temp.complain or '',
                    })
            records.append({
                'cus_name': order.partner_id.name or '',
                'pay_rec': order.name or '',
                'memo': order.payment_id.ref or '',
                'p_date': print_date.strftime('%d-%m-%Y %I:%M:%S %p'),
                'date': order.date.strftime('%d-%m-%Y'),
                'collector': order.collector or '',
                'branch': order.branch or '',
                'amount': '{:,.0f}'.format(order.amount) or '',
                'report_template_id': report_template_id,

            })
        return self.env.ref('payment_receipt_report.action_payment_receipt_a4_pdf_report').report_action(self, data={'records': records,})
