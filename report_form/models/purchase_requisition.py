import datetime
import json
from odoo import models, fields, api, _
from datetime import timedelta
from dateutil.relativedelta import relativedelta


class PurchaseAgreement(models.Model):
    _inherit = 'purchase.requisition'

    def get_local_po_agreement_a4_pdf(self):
        records = []
        lines = []
        no = 1

        for order in self:
            for line in order.line_ids:
                lines.append({
                    'no': no,
                    'pname': line.product_id.name or '',
                    'qty': '{0:,.0f}'.format(line.product_qty) or 0,
                    'uom': line.product_uom_id.name if line.product_uom_id else '',
                    'unit_price': '{0:,.2f}'.format(line.price_unit) if line.price_unit else '0',
                    'subtotal': '{0:,.2f}'.format(line.price_subtotal) if line.price_subtotal else '0',
                    'ordering_date': line.ordering_date or '',
                    'delivery_date': order.schedule_date or '',
                    'line_remark': line.line_remark or '',
                })
                no += 1

            records.append({
                'supplier_name': order.vendor_id.name or '',
                'dept_name': order.company_id.name or '',
                'sr_no': order.origin or '',
                'date': order.ordering_date or '',
                'price_validate': order.price_validate or '',
                'payment_terms': order.payment_terms or '',
                'order_confirm': order.order_confirm or '',
                'delivery': order.delivery or '',
                'remark': order.remark or '',
                'lines': lines,
            })
            return self.env.ref('report_form.action_local_po_agreement_a4_pdf_report').report_action(self, data={
                'records': records,
            })

    def get_foreign_po_agreement_a4_pdf(self):
        records = []
        lines = []
        no = 1

        for order in self:
            for line in order.line_ids:
                lines.append({
                    'no': no,
                    'pname': line.product_id.name or '',
                    'qty': '{0:,.0f}'.format(line.product_qty) or 0,
                    'uom': line.product_uom_id.name if line.product_uom_id else '',
                    'unit_price': '{0:,.2f}'.format(line.price_unit) if line.price_unit else '0',
                    'subtotal': '{0:,.2f}'.format(line.price_subtotal) if line.price_subtotal else '0',
                    'ordering_date': line.ordering_date or '',
                    'delivery_date': order.schedule_date or '',
                    'line_remark': line.line_remark or '',
                })
                no += 1

            records.append({
                'supplier_name': order.vendor_id.name or '',
                'dept_name': order.company_id.name or '',
                'sr_no': order.origin or '',
                'date': order.ordering_date or '',
                'price_validate': order.price_validate or '',
                'payment_terms': order.payment_terms or '',
                'order_confirm': order.order_confirm or '',
                'delivery': order.delivery or '',
                'remark': order.remark or '',
                'lines': lines,
            })
            return self.env.ref('report_form.action_foreign_po_agreement_a4_pdf_report').report_action(self, data={
                'records': records,
            })
