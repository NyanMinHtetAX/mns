import json
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class SaleOrder(models.Model):

    _inherit = 'sale.order'

    ks_global_discount_type = fields.Selection([('percent', 'Percentage'), ('amount', 'Amount')],
                                               string='Universal Discount Type',
                                               readonly=True,
                                               states={'draft': [('readonly', False)], 'sent': [('readonly', False)]},
                                               default='percent')
    ks_global_discount_rate = fields.Float('Universal Discount Amt',
                                           readonly=True,
                                           states={'draft': [('readonly', False)], 'sent': [('readonly', False)]})
    ks_amount_discount = fields.Monetary(string='Universal Discount',
                                         readonly=True,
                                         compute='_amount_all',
                                         store=True,
                                         tracking=5)
    ks_enable_discount = fields.Boolean(compute='ks_verify_discount')

    @api.depends('order_line.tax_id',
                 'order_line.price_unit',
                 'order_line.discount_amt',
                 'order_line.discount_type',
                 'order_line.discount_amount',
                 'amount_total', 'amount_untaxed')
    def _compute_tax_totals_json(self):
        def compute_taxes(order_line):
            if order_line.discount_type == 'percentage':
                price_unit = (order_line.price_unit * order_line.product_uom_qty) * (1 - (order_line.discount_amt or 0.0) / 100.0)
            else:
                price_unit = (order_line.price_unit * order_line.product_uom_qty) - order_line.discount_amount

            order = order_line.order_id
            return order_line.tax_id._origin.compute_all(price_unit,
                                                         order.currency_id,
                                                         product=order_line.product_id,
                                                         partner=order.partner_shipping_id)

        account_move = self.env['account.move']
        for order in self:
            tax_lines_data = account_move._prepare_tax_lines_data_for_totals_from_object(order.order_line,
                                                                                         compute_taxes)
            tax_totals = account_move._get_tax_totals(order.partner_id, tax_lines_data, order.amount_total,
                                                      order.amount_untaxed, order.currency_id)
            order.tax_totals_json = json.dumps(tax_totals)

    @api.depends('company_id.ks_enable_discount')
    def ks_verify_discount(self):
        for rec in self:
            rec.ks_enable_discount = rec.company_id.ks_enable_discount

    @api.depends('order_line.price_total', 'ks_global_discount_rate', 'ks_global_discount_type')
    def _amount_all(self):
        res = super(SaleOrder, self)._amount_all()
        for rec in self:
            if not ('ks_global_tax_rate' in rec):
                rec.ks_calculate_discount()
        return res

    def _prepare_invoice(self):
        res = super(SaleOrder, self)._prepare_invoice()
        for rec in self:
            res['ks_global_discount_rate'] = rec.ks_global_discount_rate
            res['ks_global_discount_type'] = rec.ks_global_discount_type
        return res

    def ks_calculate_discount(self):
        for rec in self:
            if rec.ks_global_discount_type == "amount":
                rec.ks_amount_discount = rec.ks_global_discount_rate if rec.amount_untaxed > 0 else 0

            elif rec.ks_global_discount_type == "percent":
                if rec.ks_global_discount_rate != 0.0:
                    rec.ks_amount_discount = (rec.amount_untaxed + rec.amount_tax) * rec.ks_global_discount_rate / 100
                else:
                    rec.ks_amount_discount = 0
            elif not rec.ks_global_discount_type:
                rec.ks_amount_discount = 0
                rec.ks_global_discount_rate = 0
            rec.amount_total = rec.amount_untaxed + rec.amount_tax - rec.ks_amount_discount

    @api.constrains('ks_global_discount_rate')
    def ks_check_discount_value(self):
        if self.ks_global_discount_type == "percent":
            if self.ks_global_discount_rate > 100 or self.ks_global_discount_rate < 0:
                raise ValidationError('You cannot enter percentage value greater than 100.')
        else:
            if self.ks_global_discount_rate < 0 or self.ks_global_discount_rate > self.amount_untaxed:
                raise ValidationError(
                    'You cannot enter discount amount greater than actual cost or value lower than 0.')


class SaleOrderLine(models.Model):

    _inherit = 'sale.order.line'

    @api.depends('price_unit', 'product_uom_qty', 'discount_type', 'discount_amt')
    def _get_discount_amount(self):
        for record in self:
            if record.discount_type == 'percentage':
                discount_amt = (record.price_unit * record.product_uom_qty) * ((record.discount_amt or 0.0) / 100.0)
            else:
                discount_amt = record.product_uom_qty * record.discount_amt
            record.update({'discount_amount': discount_amt})

    discount_type = fields.Selection(selection=[('percentage', 'Percentage'),
                                                ('fixed', 'Fixed')],
                                     string='Disc Type',
                                     default="fixed")
    discount_amt = fields.Float(string='Dis/Refund')
    discount_amount = fields.Float(string='Dis Amt', compute='_get_discount_amount',store=True)

    @api.depends('product_uom_qty', 'discount_type', 'discount', 'discount_amt',
                 'discount_amount', 'price_unit', 'tax_id')
    def _compute_amount(self):
        for line in self:
            if line.discount_type == 'percentage':
                price_unit = (line.price_unit * line.product_uom_qty) * (1 - (line.discount_amt or 0.0) / 100.0)
            else:
                price_unit = (line.price_unit * line.product_uom_qty) - line.discount_amount
            price_subtotal = price_unit
            taxes = line.tax_id.compute_all(price_subtotal,
                                            line.order_id.currency_id,
                                            product=line.product_id,
                                            partner=line.order_id.partner_shipping_id)
            line.update({
                'price_tax': sum(t.get('amount', 0.0) for t in taxes.get('taxes', [])),
                'price_total': taxes['total_included'],
                'price_subtotal': taxes['total_excluded'],
            })

    def _prepare_invoice_line(self, **optional_values):
        res = super(SaleOrderLine, self)._prepare_invoice_line(**optional_values)
        res.update({
            'discount_type': self.discount_type,
            'discount': self.discount_amt,
            'discount_amount': self.discount_amount,
        })
        return res


class SaleAdvancePaymentInv(models.TransientModel):

    _inherit = "sale.advance.payment.inv"

    def _create_invoice(self, order, so_line, amount):
        invoice = super(SaleAdvancePaymentInv, self)._create_invoice(order, so_line, amount)
        if invoice:
            invoice['ks_global_discount_rate'] = order.ks_global_discount_rate
            invoice['ks_global_discount_type'] = order.ks_global_discount_type
        return invoice
