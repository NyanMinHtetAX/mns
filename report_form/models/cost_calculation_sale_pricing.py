from odoo import api, models, fields, _
from decimal import Decimal, ROUND_DOWN

class CostCalculationSalePricing(models.Model):
    _inherit = 'cost.calculation.sale.pricing'

    def get_cost_calculation_pdf(self):
        records = []
        status = ''
        lines = []
        for rec in self:
            if rec.lines_ids:
                no = 1

                for line in rec.lines_ids:
                    lines.append({
                        'no': no,
                        'name': line.product_id.name if line.product_id else '',
                        'qty': line.qty or '',
                        'cost': '{0:,.2f}'.format(line.cost) if line.cost else '',
                        'cost_charge': '{0:,.2f}'.format(line.cost_charge) if line.cost_charge else '',
                        'cost_charge_percentage': '{0:,.2f}'.format(line.cost_charge_percentage) if line.cost_charge_percentage else '',
                        'commission_charge': '{0:,.2f}'.format(line.commission_charge) if line.commission_charge else '',
                        'commission_charge_percentage': '{0:,.2f}'.format(line.commission_charge_percentage) if line.commission_charge_percentage else '',
                        'sale': '{0:,.2f}'.format(line.sale_price) if line.sale_price else '',
                        'profit': '{0:,.2f}'.format(line.profit) if line.profit else '',
                        'profit_percentage': '{0:,.2f}'.format(line.profit_percentage * 100) if line.profit_percentage else '',
                        'loss': '{0:,.2f}'.format(line.loss) if line.loss else '',
                        'loss_percentage': '{0:,.2f}'.format(line.loss_percentage * 100) if line.loss_percentage else '',
                        'cost_price': '{0:,.2f}'.format(line.cost_price) if line.cost_price else '',
                        'cost_price_percentage': '{0:,.2f}'.format(line.cost_price_percentage * 100) if line.cost_price_percentage else '',
                        'total_sale_price': '{0:,.2f}'.format(line.total_sale_price) if line.total_sale_price else '',
                        'total_sale_profit': '{0:,.2f}'.format(line.total_sale_profit) if line.total_sale_profit else '',
                        'total_sale_loss': '{0:,.2f}'.format(line.total_sale_lose) if line.total_sale_lose else '',
                        'remark': line.remark or '',
                    })
                    no+=1
            records.append({
                'date': rec.date.strftime('%d-%m-%Y') if rec.date else '',
                'department': rec.department_id.name if rec.department_id else '',
                'department_branch': rec.department_branch or '',
                'lines': lines,
            })
            return self.env.ref('report_form.action_cost_calculation_pdf').report_action(self, data={
                'records': records,
            })
