import datetime
import json
from odoo import models, fields, api, _
from datetime import timedelta
from dateutil.relativedelta import relativedelta


class ProductionOrderSummary(models.Model):
    _inherit = 'production.order.summary'

    def get_production_order_summary_a4_pdf(self):
        records = []
        product_lines = []
        raw_component_lines = []
        p_index = 1
        raw_index = 1

        for order in self:
            price_unit_prec = self.env['decimal.precision'].precision_get('Product Price')
            qty_prec = self.env['decimal.precision'].precision_get('Product Unit of Measure')
            qty_dec_len = 0
            dec_len = 0
            if price_unit_prec:
                dec_len += price_unit_prec
            else:
                dec_len += 2

            if qty_prec:
                qty_dec_len += qty_prec
            else:
                qty_dec_len += 3
            for line in order.production_product_lines_ids:
                product_lines.append({
                    'no': p_index,
                    'pname': line.bom_product_id.product_tmpl_id.name or '',
                    'qty': '{0:,.{len}f}'.format(line.qty, len=qty_dec_len) or '0.000',
                    'uom': line.uom_id.name if line.uom_id else '',
                    'weight': '{0:,.{len}f}'.format(line.weight, len=qty_dec_len) or '0.000',
                    'to_product_qty': '{0:,.{len}f}'.format(line.to_product_weight, len=qty_dec_len) or '0.000',
                })
                p_index += 1

            for line in order.production_raw_components_ids:
                raw_component_lines.append({
                    'no': raw_index,
                    'pname': line.product_id.name or '',
                    'qty': '{0:,.{len}f}'.format(line.qty, len=qty_dec_len) or '0.000',
                    'uom': line.uom_id.name if line.uom_id else '',
                    'bal_qty': '{0:,.{len}f}'.format(line.total_onhand_qty, len=qty_dec_len) or '0.000',
                    'overed_qty': '{0:,.{len}f}'.format(line.overed_qty, len=qty_dec_len) or '0.000',
                    'required_qty': '{0:,.{len}f}'.format(line.required_qty, len=qty_dec_len) or '0.000',
                    'unit_price': '{0:,.{len}f}'.format(line.unit_price, len=dec_len) if line.unit_price else '0.00000',
                    'amount_unit': '{0:,.{len}f}'.format(line.amount_unit, len=dec_len) if line.amount_unit else '0.00000',
                    'amount_currency_rate': '{0:,.{len}f}'.format(line.amount_currency_rate, len=dec_len) if line.amount_currency_rate else '0.00000',
                })
                raw_index += 1
            confirmed_date = False
            if order.confirmed_date:
                confirmed_date = order.confirmed_date + relativedelta(hours=6, minutes=30)

            records.append({
                'currency_rate': '{0:,.2f}'.format(order.currency_rate) or '0.00',
                'qty_kg': '{0:,.{len}f}'.format(order.qty_kg, len=qty_dec_len) or '0.000',
                'created_date': order.created_date + relativedelta(hours=6, minutes=30) or '',
                'confirmed_date': confirmed_date or '',
                'total_product_lines_qty': '{0:,.{len}f}'.format(order.total_product_lines_qty, len=qty_dec_len) or '0.000',
                'total_product_weight': '{0:,.{len}f}'.format(order.total_product_weight, len=qty_dec_len) or '0.000',
                'total_components_qty': '{0:,.{len}f}'.format(order.total_components_qty, len=qty_dec_len) or '0.000',
                'total_components_amount_unit': '{0:,.{len}f}'.format(order.total_components_amount_unit, len=dec_len) or '0.00000',
                'total_components_amount_currency': '{0:,.{len}f}'.format(order.total_components_amount_currency, len=dec_len) or '0.00000',
                'product_lines': product_lines,
                'raw_component_lines': raw_component_lines,
            })
            return self.env.ref('report_form.action_production_order_summary_a4_pdf_report').report_action(self, data={
                'records': records,
            })
