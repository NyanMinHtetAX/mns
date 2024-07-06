import json
from tokenize import group
from odoo import api, models, fields, _
from datetime import timedelta
import datetime
import math
from odoo.exceptions import UserError
from dateutil.relativedelta import relativedelta
import urllib.parse as urllp


class AccountMove(models.Model):
    _inherit = 'account.move'

    remark = fields.Text('Remark')
    picking_type_id = fields.Many2one('stock.picking.type', string='Delivery To')
    purchaser_employee_id = fields.Many2one('hr.employee', string='Purchaser')
    po_number = fields.Char('Source')

    def get_vendor_bill_pdf_report(self):
        index = 1
        records = []
        for order in self:
            amount_total = json.loads(order.tax_totals_json)
            if amount_total:
                total = amount_total.get('amount_total')

            report_template_id = []
            if order.report_template_id:
                for temp in order.report_template_id:
                    report_template_id.append({
                        'title_img': temp.image_1920 or False,
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

            invoice_line_ids = []
            total_discount = sum(order.invoice_line_ids.mapped('discount'))
            total_qty = sum(order.invoice_line_ids.mapped('quantity'))
            total_foc = sum(order.invoice_line_ids.mapped('purchase_foc_id.id'))
            for line in order.invoice_line_ids:
                invoice_line_ids.append({
                    'no': index,
                    'code': line.product_id.default_code or '',
                    'description': line.product_id.name or '',
                    'uom': line.product_uom_id.name or '',
                    'qty': line.quantity or '',
                    'pur_price': math.floor(line.price_unit) or '0',
                    'discount': math.floor(line.discount) or '0',
                    'tax': line.tax_ids.id or '0',
                    'subtotal': line.price_subtotal or '0',
                })
                index += 1

            amount = 0
            payments_info = json.loads(order.invoice_payments_widget)
            if payments_info:
                contents = payments_info.get('content')
                for content in contents:
                    amount += content.get('amount')
            # else:
            #     payments_info = json.loads('{}')

            records.append({
                'printed_date': datetime.datetime.now().strftime('%d-%m-%Y %I:%M:%S %p'),
                'bill_no': order.name or '',
                'supplier': order.partner_id.name or '',
                'purchaser': order.purchaser_employee_id.name or '',
                'bill_date': (order.invoice_date + timedelta(hours=6, minutes=30)).strftime("%d/%m/%Y") or '',
                'due_date': (order.invoice_date_due + timedelta(hours=6, minutes=30)).strftime("%d/%m/%Y") or '',
                'source': order.po_number or '',
                'location': order.picking_type_id.warehouse_id.name or '',
                'remark': order.remark or '',
                'total_foc': total_foc or '0',
                'total_qty': total_qty or '0',
                'total_discount': math.floor(total_discount) or '0',
                'total': total or 0,
                'paid_amount': amount or '0',
                'net_amount': order.total_amount or '0',
                'invoice_line_ids': invoice_line_ids,
                'report_template_id': report_template_id,
            })
        # 
        return self.env.ref('dynamic_pdf_report.action_vendor_bill_pdf_report').report_action(self, data={'records': records}) 

    def get_invoice_pdf_report(self, return_data = False):
        company = False
        records = []
        no = 1
        print_date = datetime.datetime.now() + relativedelta(hours=6, minutes=30)
        for order in self:
            company = []
            line = []
            contact = False
            child_ids = order.partner_id.child_ids
            for con in child_ids:
                if con.type == 'contact':
                    contact = con.name
            total = 0.0
            payment_type = 'Cash'
            discount_total = 0
            qty_total = 0
            foc_total = 0
            report_template_id = []
            if order.report_template_id:
                for temp in order.report_template_id:
                    report_template_id.append({
                        'title_img': temp.image_1920 or False,
                        'title1': temp.title1 or '',
                        'title2': temp.title2 or '',
                        'address': temp.address or '',
                        'company_phone': temp.company_phone,
                        'social_viber': temp.social_viber or '',
                        'social_mail': temp.social_mail or '',
                        'thank': temp.thank or '',
                        'complain': temp.complain or '',
                        'remark_note': temp.remark_note or '',
                    })
            else:
                raise UserError(_('Please Insert Report Template '))

            for lines in order.invoice_line_ids:
                discount_total += lines.discount_amount
                qty_total += lines.multi_uom_qty
                if lines.is_foc:
                    foc_total += 1
                line.append({
                    'no': no,
                    'o_pcode': lines.product_id.default_code or '',
                    'o_pname': lines.product_id.name or '',
                    'o_qty': '{0:,.0f}'.format(lines.multi_uom_qty) or 0,
                    'o_uom_unit': lines.multi_uom_line_id.uom_id.name or '',
                    'o_uom': lines.uom_ratio_remark or '',
                    'o_punit': '{0:,.0f}'.format(lines.multi_price_unit) or 0,
                    'o_discount': '{0:,.0f}'.format(lines.discount_amount) or 0,
                    'o_tax': lines.tax_ids.name or '',
                    'o_subtotal': '{0:,.0f}'.format(lines.price_subtotal) or 0,
                })
                no += 1

            company.append({
                'printed_date': print_date.strftime('%d-%m-%Y %I:%M:%S %p'),
                'company_name': order.company_id.name or '',
                'image': order.company_id.logo or '',
                'phone': order.company_id.phone or '',
                'street1': order.company_id.street or '',
                'street2': order.company_id.street2 or '',
                'township': order.company_id.township_id.name or '',
                'city': order.company_id.city or '',
                'gmail': order.company_id.email or '',
                'website': order.company_id.website or '',
                'facebook_link': order.company_id.partner_id.facebook_link or '',
                'viber_no': order.company_id.partner_id.viber_no or '',
                'we_chat': order.company_id.partner_id.we_chat or '',
            })
            if order.payment_type == 'partial':
                payment_type = 'Partial'
            elif order.payment_type == 'credit':
                payment_type = 'Credit'
            else:
                payment_type = 'Cash'

            amount = 0
            payments_info = json.loads(order.invoice_payments_widget)
            if payments_info:
                contents = payments_info.get('content')
                for content in contents:
                    amount += content.get('amount')

            grand_total = order.amount_untaxed - amount + order.total_due
            records.append({
                'invoice_id': order.name or '',
                'payment_type': payment_type or '',
                'cus_name': contact or '',
                'shop_name': order.partner_id.name or '',
                'township': order.partner_id.township_id.name or '',
                'city': order.partner_id.x_city_id.name or '',
                'customer_code': order.partner_id.ref or '',
                'sale_person': order.invoice_user_id.name or '',
                'due_date': order.invoice_date_due.strftime('%d-%m-%Y') if order.invoice_date_due else '',
                'invoice_date': order.invoice_date.strftime('%d-%m-%Y') if order.invoice_date else '',
                'remark': order.remark or '',
                'foc_amount': '{0:,.0f}'.format(order.foc_amount) or 0,
                'source': order.invoice_origin or '',
                'sub_total': '{0:,.0f}'.format(order.amount_untaxed) or 0,
                'paid_amount': '{0:,.0f}'.format(amount) or 0,
                'due_amount': '{0:,.0f}'.format(order.total_due) or 0,
                'grand_total': '{0:,.0f}'.format(grand_total) or 0,
                'discount_total': '{0:,.0f}'.format(discount_total) or '',
                'qty_total': '{0:,.0f}'.format(qty_total) or '',
                'foc_total': '{0:,.0f}'.format(foc_total) or '',
                'lines': line,
                'report_template_id': report_template_id,
            })
        #
        if return_data:
            return {
            'company': company,
            'records': records,
        }
        # return records, company
        return self.env.ref('dynamic_pdf_report.action_invoice_b5_pdf_report').report_action(self, data={
            'company': company,
            'records': records,
        })

    def preview_invoice(self):
        self.ensure_one()

        if not self.report_template_id:
            raise UserError(_('Please Insert Report Template '))
        return {
            'type': 'ir.actions.act_url',
            'url': f'/ax/preview_py3o_pdf?file_name={self._get_report_base_filename()}_{self.id}',
        }

class AccountMoveLine(models.Model):

    _inherit = 'account.move.line'

    purchase_foc_id = fields.Many2one('purchase.foc', 'Purchase FOC')
