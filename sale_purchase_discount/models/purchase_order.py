from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class PurchaseOrder(models.Model):

    _inherit = 'purchase.order'

    ks_global_discount_type = fields.Selection([('percent', 'Percentage'), ('amount', 'Amount')],
                                               string='Global Discount Type', readonly=True,
                                               states={'draft': [('readonly', False)], 'sent': [('readonly', False)]},
                                               default='percent')
    ks_global_discount_rate = fields.Float('Global Discount Rate', readonly=True,
                                           states={'draft': [('readonly', False)], 'sent': [('readonly', False)]})
    ks_amount_discount = fields.Monetary(string='Global Discount', readonly=True, compute='_amount_all',
                                         store=True)
    ks_enable_discount = fields.Boolean(compute='ks_verify_discount')

    @api.depends('order_line.price_total', 'ks_global_discount_type', 'ks_global_discount_rate')
    def _amount_all(self):
        for order in self:
            amount_untaxed = amount_tax = total_discount = 0.0
            for line in order.order_line:
                amount_untaxed += line.price_subtotal
                if line.discount_type == 'fixed':
                    total_discount += line.discount
                else:
                    total_discount += line.price_unit * line.product_qty * ((line.discount or 0.0) / 100.0)
                if order.company_id.tax_calculation_rounding_method == 'round_globally':
                    quantity = 1.0
                    if line.discount_type == 'fixed':
                        price = line.price_unit * line.product_qty - (line.discount or 0.0)
                    else:
                        quantity = line.product_qty
                        price = line.price_unit * (1 - (line.discount or 0.0) / 100.0)
                    taxes = line.taxes_id.compute_all(price, line.order_id.currency_id, quantity,
                                                      product=line.product_id, partner=line.order_id.partner_id)
                    amount_tax += sum(t.get('amount', 0.0) for t in taxes.get('taxes', []))
                else:
                    amount_tax += line.price_tax

            IrConfigPrmtrSudo = self.env['ir.config_parameter'].sudo()
            discTax = IrConfigPrmtrSudo.get_param('purchase.global_discount_tax_po')

            if discTax == 'taxed':
                total = amount_untaxed + amount_tax
            else:
                total = amount_untaxed

            if discTax != 'taxed':
                total += amount_tax
            currency = order.currency_id or order.partner_id.property_purchase_currency_id or self.env.company.currency_id
            order.update({
                'amount_untaxed': currency.round(amount_untaxed),
                'amount_tax': currency.round(amount_tax),
                'amount_total': total,
            })
            if not ('global_tax_rate' in order):
                order.ks_calculate_discount()

    @api.depends('company_id.ks_enable_discount')
    def ks_verify_discount(self):
        for rec in self:
            rec.ks_enable_discount = rec.company_id.ks_enable_discount

    def _prepare_invoice(self):
        res = super(PurchaseOrder, self)._prepare_invoice()
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
            rec.amount_total = rec.amount_tax + rec.amount_untaxed - rec.ks_amount_discount

    @api.constrains('ks_global_discount_rate')
    def ks_check_discount_value(self):
        if self.ks_global_discount_type == "percent":
            if self.ks_global_discount_rate > 100 or self.ks_global_discount_rate < 0:
                raise ValidationError('You cannot enter percentage value greater than 100.')
        else:
            if self.ks_global_discount_rate < 0 or self.ks_global_discount_rate > self.amount_untaxed:
                raise ValidationError(
                    'You cannot enter discount amount greater than actual cost or value lower than 0.')


class PurchaseOrderLine(models.Model):

    _inherit = "purchase.order.line"

    discount_type = fields.Selection(selection=[('percentage', 'Percentage'), ('fixed', 'Fixed')],
                                     string='Disc Type', default="fixed")
    discount = fields.Float(string="Dis/Refund")
    discount_amount = fields.Float(string="Dis Amt", compute='_get_discount_amount', store=True)

    @api.depends('price_unit', 'product_qty', 'discount_type', 'discount')
    def _get_discount_amount(self):
        for record in self:
            if record.discount_type == 'percentage':
                discount_amt = record.price_unit * ((record.discount or 0.0) / 100.0) * record.product_qty
            else:
                discount_amt = record.product_qty * record.discount

            record.update({
                'discount_amount': discount_amt
            })

    @api.depends('product_qty', 'price_unit', 'taxes_id', 'discount_type', 'discount', 'discount_amount')
    def _compute_amount(self):
        return super(PurchaseOrderLine, self)._compute_amount()

    def _prepare_compute_all_values(self):
        res = super(PurchaseOrderLine, self)._prepare_compute_all_values()
        price_unit = res['price_unit']
        product_qty = res['quantity']

        if self.discount_type == 'percentage':
            price_unit = price_unit * (1 - (self.discount or 0.0) / 100.0)
        else:
            price_unit = (price_unit * product_qty) - (self.discount * product_qty)
            product_qty = 1.0

        res['price_unit'] = price_unit
        res['quantity'] = product_qty
        return res

    def _prepare_account_move_line(self, move=False):
        res = super(PurchaseOrderLine, self)._prepare_account_move_line(move=move)
        res.update({
            'discount_type': self.discount_type,
            'discount': self.discount,
            'discount_amount': self.discount_amount,
        })
        return res
