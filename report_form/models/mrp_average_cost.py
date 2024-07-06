from odoo import api, models, fields, _
from decimal import Decimal, ROUND_DOWN


class MRPRawAverageCost(models.Model):
    _inherit = 'mrp.raw.material.average.cost'

    def format_amount(self, amt, currency):
        print('format_amount', currency, amt, currency.symbol, currency.position)
        if currency.position == 'after':
            return f'{amt} {currency.symbol}'
        else:
            return f'{currency.symbol or ""} {amt}'

    def get_raw_ac_finish_cost_pdf(self):
        records = []
        status = ''
        lines = []

        for rec in self:
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
            currency = self.env.company.currency_id
            records.append({
                'date': rec.date.strftime('%d-%m-%Y') if rec.date else '',
                'product': rec.bom_id.product_tmpl_id.display_name if rec.bom_id else '',
                'weight': '{0:,.2f}'.format(rec.weight) if rec.weight else '0.00',
                'cost1kg': '{0:,.{len}f}'.format(rec.total_cost_per_kg, len=dec_len) if rec.total_cost_per_kg else '0.00',
                'p_cost': '{0:,.{len}f}'.format(rec.cost_for_product, len=dec_len) if rec.cost_for_product else '0.00',
                'packing': '{0:,.{len}f}'.format(rec.total_packing_cost, len=dec_len) if rec.total_packing_cost else '0.00',
                'finish_good_cost': '{0:,.{len}f}'.format(rec.finish_good_cost, len=dec_len) if rec.finish_good_cost else '0.00',
            })
            return self.env.ref('report_form.action_mrp_ac_finish_cost_pdf').report_action(self, data={
                'records': records,
            })

    def get_raw_ac_packing_pdf(self):
        records = []
        status = ''
        lines = []
        no = 1
        for rec in self:
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
            currency = self.env.company.currency_id
            if rec.packing_cost_lines:
                for line in rec.packing_cost_lines:
                    lines.append({
                        'no': no,
                        'name': line.packing_id.product_id.display_name if line.packing_id and line.packing_id.product_id else '',
                        'qty': '{0:,.{len}f}'.format(line.qty, len=qty_dec_len),
                        'price': '{0:,.{len}f}'.format(line.cost, len=dec_len) if line.cost else '0.00',
                        'amount': '{0:,.{len}f}'.format(line.price_amount, len=dec_len) if line.price_amount else '0.00',
                        'remark': line.remark or '',
                    })
                    no += 1
            records.append({
                'date': rec.date.strftime('%d-%m-%Y') if rec.date else '',
                'product': rec.bom_id.product_tmpl_id.display_name if rec.bom_id else '',
                'qty': '{0:,.{len}f}'.format(rec.qty, len=qty_dec_len) if rec.qty else '0.00',
                'uom': rec.uom_id.name if rec.uom_id else '',
                'time': rec.time or '',
                'total_packing': '{0:,.{len}f}'.format(rec.total_packing_cost, len=dec_len) if rec.total_packing_cost else '0.00',
                'lines': lines,
            })
            return self.env.ref('report_form.action_mrp_ac_packing_pdf').report_action(self, data={
                'records': records,
            })
