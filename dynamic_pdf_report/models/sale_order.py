from dateutil.relativedelta import relativedelta

from odoo import api, models, fields, _
from odoo.exceptions import UserError
import datetime


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    def action_confirm(self):
        res = super(SaleOrder, self).action_confirm()
        for rec in self:
            rec.picking_ids.write({'sale_person_id': rec.user_id.id})
        return res

    def get_sale_order_pdf_report(self):
        for order in self:
            records = []
            company = []
            line = []
            discount_total = 0
            qty_total = 0
            foc_total = 0
            no = 1
            contact = False
            child_ids = order.partner_id.child_ids
            for con in child_ids:
                if con.type == 'contact':
                    contact = con.name
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

            for lines in order.order_line:
                discount_total += lines.discount_amount
                qty_total += lines.multi_uom_qty
                print_date = datetime.datetime.now() + relativedelta(hours=6, minutes=30)
                if lines.is_foc:
                    foc_total += 1
                line.append({
                    'no': no,
                    'o_pcode': lines.product_id.default_code or '',
                    'o_pname': lines.product_id.name or '',
                    'o_qty': lines.multi_uom_qty or 0,
                    'o_uom': lines.multi_uom_line_id.uom_id.name or '',
                    'o_punit': '{0:,.1f}'.format(lines.multi_price_unit) or 0.0,
                    'o_discount': '{0:,.1f}'.format(lines.discount_amount) or 0.0,
                    'o_tax': lines.tax_id.name or '',
                    'o_subtotal': '{0:,.1f}'.format(lines.price_subtotal) or 0.0,
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
            records.append({
                'cus_name': contact or '',
                'order_ref': order.name or '',
                'order_date': order.date_order.strftime('%d-%m-%Y') or '',
                'township': order.partner_id.township_id.name or '',
                'city': order.partner_id.x_city_id.name or '',
                'customer_code': order.partner_id.ref or '',
                'shop': order.partner_id.company_register_id or '',
                'sale_person': order.user_id.name or '',
                'remark': order.remark or '',
                'foc_amount': order.foc_amount or 0.0,
                'sub_total': '{0:,.1f}'.format(order.amount_untaxed) or 0.0,
                'grand_total': '{0:,.1f}'.format(order.amount_total) or 0.0,
                'discount_total': '{0:,.1f}'.format(discount_total) or '',
                'qty_total': qty_total or '',
                'foc_total': foc_total or '',
                'lines': line,
                'report_template_id': report_template_id,
            })
        return self.env.ref('dynamic_pdf_report.action_sale_order_b5_pdf_report').report_action(self, data={
            'company': company,
            'records': records,
        })
