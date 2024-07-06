from dateutil.relativedelta import relativedelta

from odoo import api, models, fields, _
import datetime
from odoo.exceptions import UserError

from odoo.tools import json


class AccountMove(models.Model):
    _inherit = 'account.move'

    def get_invoice_pdf_report(self):
        records = []
        company = []
        line = []
        total = 0.0
        payment_type = 'Cash'
        discount_total = 0
        qty_total = 0
        foc_total = 0
        no = 1
        print_date = datetime.datetime.now() + relativedelta(hours=6, minutes=30)
        report_template_id = []

        for lines in self.invoice_line_ids:
            discount_total += lines.discount_amount
            qty_total += lines.multi_uom_qty
            report_template_id = []
            if self.report_template_id:
                for temp in self.report_template_id:
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
            else:
                raise UserError(_('Please Insert Report Template '))
            if lines.is_foc:
                foc_total += 1
            line.append({
                'no': no,
                'o_pcode': lines.product_id.default_code or '',
                'o_pname': lines.product_id.name or '',
                'o_qty': lines.multi_uom_qty or 0,
                'o_uom_unit': lines.multi_uom_line_id.uom_id.name or '',
                'o_uom': lines.uom_ratio_remark or '',
                'o_punit': '{0:,.1f}'.format(lines.multi_price_unit) or 0.0,
                'o_discount': '{0:,.1f}'.format(lines.discount_amount) or 0.0,
                'o_tax': lines.tax_ids.name or '',
                'o_subtotal': '{0:,.1f}'.format(lines.price_subtotal) or 0.0,
            })
            no += 1

        company.append({
            'printed_date': print_date.strftime('%d-%m-%Y %I:%M:%S %p'),
            'company_name': self.company_id.name,
            'image': self.company_id.logo,
            'phone': self.company_id.phone or '',
            'street1': self.company_id.street or '',
            'street2': self.company_id.street2 or '',
            'township': self.company_id.township_id.name or '',
            'city': self.company_id.city or '',
            'gmail': self.company_id.email or '',
            'website': self.company_id.website or '',
            'facebook_link': self.company_id.partner_id.facebook_link or '',
            'viber_no': self.company_id.partner_id.viber_no or '',
            'we_chat': self.company_id.partner_id.we_chat or '',
        })
        if self.payment_type == 'partial':
            payment_type = 'Partial'
        elif self.payment_type == 'credit':
            payment_type = 'Credit'
        else:
            payment_type = 'Cash'
        if self.partner_id.child_ids:

            records.append({
                'invoice_id': self.name,
                'payment_type': payment_type,
                'cus_name': self.partner_id.child_ids[-1].name or '',
                'shop_name': self.partner_id.name or '',
                'township': self.partner_id.township_id.name or '',
                'city': self.partner_id.x_city_id.name or '',
                'customer_code': self.partner_id.ref or '',
                'sale_person': self.invoice_user_id.name or '',
                'due_date': self.invoice_date_due.strftime('%d-%m-%Y') or '',
                'invoice_date': self.invoice_date.strftime('%d-%m-%Y') or '',
                'remark': self.remark or '',
                'foc_amount': self.foc_amount or 0.0,
                'source': self.invoice_origin or '',
                'sub_total': '{0:,.1f}'.format(self.amount_untaxed) or 0.0,
                'paid_amount': '{0:,.1f}'.format(self.amount_total) or 0.0,
                'due_amount': '{0:,.1f}'.format(self.total_due) or 0.0,
                'grand_total': '{0:,.1f}'.format(self.total_amount + self.amount_residual) or 0.0,
                'discount_total': '{0:,.1f}'.format(discount_total),
                'qty_total': qty_total,
                'foc_total': foc_total,
                'lines': line,
                'report_template_id': report_template_id,
            })
            return self.env.ref('report_form.action_invoice_b5_pdf_report').report_action(self, data={
                'company': company,
                'records': records,
            })
        else:
            raise UserError(_('Please insert contact addresses in customer form'))
