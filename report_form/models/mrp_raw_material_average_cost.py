from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class MrpRawMaterialAverageCost(models.Model):
    _inherit = 'mrp.raw.material.average.cost'

    def format_amount(self, amt, currency):
        if not currency.id:
            return amt
        if currency.position == 'after':
            return f'{amt} {currency.symbol}'
        else:
            return f'{currency.symbol or ""} {amt}'

    def get_report_datas(self, report_type):
        main_vals = []
        for move in self:
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

            if report_type == 'cost_for_1kg':
                lines = []
                percentage_total, litter_kg_total, rate_per_gram_total, amount_total, amount_k_total = 0, 0, 0, 0, 0

                for index, line in enumerate(move.cost_per_kg_lines):
                    val = {
                        'no': index + 1,
                        'product_name': line.bom_line_id.display_name or '',
                        'percentage': '{0:,.2f}'.format(line.percent),
                        'litter_kg': '{0:,.{len}f}'.format(line.litter_per_kg, len=dec_len),
                        'rate_per_gram': '{0:,.{len}f}'.format(line.rate_per_gram, len=dec_len) or 0.0,
                        'rate_per_kg': '{0:,.{len}f}'.format(line.rate_per_kg, len=dec_len) or 0.0,
                        'amount': '{0:,.{len}f}'.format(line.price_amount, len=dec_len) or 0.0,
                        'amount_k': '{0:,.{len}f}'.format(line.price_amount_k, len=dec_len) or 0.0,
                        'remark': line.remark,
                    }
                    percentage_total += line.percent
                    litter_kg_total += line.litter_per_kg
                    rate_per_gram_total += line.rate_per_gram
                    amount_total += line.price_amount
                    amount_k_total += line.price_amount_k
                    lines.append(val)

                vals = {
                    'date': move.date.strftime('%d-%m-%Y') if move.date else '',
                    'time': move.time,
                    'qty': '{0:,.{len}f}'.format(move.qty, len=qty_dec_len),
                    'uom_name': move.uom_id.name or '',
                    'product_name': move.bom_id.product_tmpl_id.display_name if move.bom_id else '',
                    'exchange_rate': '{0:,.{len}f}'.format(move.exchange_rate, len=dec_len),
                    'lines': lines,
                    "percentage_total": '{0:,.2f}'.format(percentage_total),
                    "litter_kg_total": '{0:,.{len}f}'.format(litter_kg_total, len=dec_len),
                    "rate_per_gram_total": '{0:,.{len}f}'.format(rate_per_gram_total, len=dec_len) or 0.0,
                    "amount_total": '{0:,.{len}f}'.format(amount_total, len=dec_len) or 0.0,
                    "amount_k_total": '{0:,.{len}f}'.format(amount_k_total, len=dec_len) or 0.0
                }

                main_vals.append(vals)

        return main_vals

    def get_raw_material_average_cost_pdf_report(self, report_type):
        records = self.get_report_datas(report_type)
        if report_type == 'cost_for_1kg':
            report_name = 'report_form.action_mrp_raw_material_cost_for_1kg_average_cost_pdf_a4_report'

        return self.env.ref(report_name).report_action(self.ids, data={
            'records': records,
        })
