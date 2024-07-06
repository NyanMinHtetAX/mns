import json
import datetime
from odoo import api, models, fields, _
from datetime import timedelta
import math
from odoo.exceptions import UserError


class PurchaseOrder(models.Model):

    _inherit = 'purchase.order'

    delivery_method = fields.Char('Delivery Method')
    remark = fields.Text('Remark')

    def _prepare_invoice(self):
        values = super(PurchaseOrder, self)._prepare_invoice()
        values.update({
            'remark': self.remark,
            'picking_type_id': self.picking_type_id,
            'po_number': self.name,
            'purchaser_id': self.purchaser_id,
        })
        return values

    def get_purchase_order_pdf_report(self):
        index = 1
        records = []
        for order in self:
            amount_total = json.loads(order.tax_totals_json)
            if amount_total:
                total = amount_total.get('amount_total')

            paid_amt = order.total_due - amount_total.get('amount_total'),

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
            else:
                raise UserError(_('Please Insert Report Template '))

            order_line = []
            total_discount = sum(order.order_line.mapped('discount_amount'))
            total_qty = sum(order.order_line.mapped('product_qty'))
            total_foc = sum(order.order_line.mapped('purchase_foc_id.id'))
            for line in order.order_line:
                order_line.append({
                    'no': index,
                    'code': line.product_id.default_code or '',
                    'description': line.product_id.name or '',
                    'uom': line.product_id.uom_id.name or '',
                    'qty': line.product_qty or '',
                    'pur_price': line.product_id.standard_price or '0',
                    'discount': math.floor(line.discount_amount) or '0',
                    'tax': line.price_tax or '0',
                    'amount': line.price_total or '0',
                })
                index += 1

            records.append({
                'printed_date': datetime.datetime.now().strftime('%d-%m-%Y %I:%M:%S %p'),
                'po_no': order.name or '',
                'supplier': order.partner_id.name or '',
                'purchaser': order.purchaser_id.name or '',
                'order_date': (order.date_approve + timedelta(hours=6, minutes=30)).strftime("%d/%m/%Y") or '',
                'receipt_date': (order.date_planned + timedelta(hours=6, minutes=30)).strftime("%d/%m/%Y") or '',
                'deli_method': order.delivery_method or '',
                'location': order.picking_type_id.warehouse_id.name or '',
                'remark': order.remark or '',

                # 'total_line_amount': order.total_untaxed,
                # 'global_discount': order.ks_amount_discount or '0',
                # 'line_discount': order.line_discount or '0',
                # 'after_line_discount': order.after_line_discount or '0',
                # 'adv_pay': order.total_due or '0',
                # 'paid_amt': paid_amt or 0,
                'total_foc': total_foc or '0',
                'total_qty': total_qty or '0',
                'total_discount': math.floor(total_discount) or '0',
                'total': total or 0,
                'order_line': order_line,
                'report_template_id': report_template_id,
            })
        return self.env.ref('dynamic_pdf_report.action_purchase_order_pdf_report').report_action(self,
                                                                                         data={'records': records})

