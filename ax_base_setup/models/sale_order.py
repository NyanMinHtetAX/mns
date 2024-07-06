from odoo import api, fields, models, exceptions, _
from odoo import SUPERUSER_ID
from odoo.exceptions import UserError


class SaleOrder(models.Model):
    _inherit = "sale.order"

    credit_limit = fields.Float('Credit Limit Amount', related='partner_id.credit_limit')
    over_credit = fields.Boolean('Disallow Credit Limit', related='partner_id.over_credit')
    total_due = fields.Monetary('Total Due Amount', readonly=True, related='partner_id.amount_due')
    sale_date = fields.Date('Date', required=True, readonly=False, default=fields.date.today())
    invoice_date_due = fields.Date('Invoice Due Date', compute='_get_date_due')
    over_payment = fields.Boolean('Unallow Payment', related='partner_id.over_payment')

    
    @api.onchange('date_order')
    def onchange_order_date(self):
        for rec in self:
            if rec.date_order:
                rec.sale_date = rec.date_order.date()

    @api.depends('partner_id')
    def _get_date_due(self):
        self.invoice_date_due = False
        if self.partner_id and self.over_credit is True or self.over_payment is True:
            invoice_date_list = []
            move = self.env['account.move'].search([('partner_id', '=', self.partner_id.id),
                                                    ('payment_state', 'in', ['not_paid','partial']),('state','!=','cancel'),('move_type','!=','out_refund')])
            for rec in move:
                if rec.invoice_date_due:
                    invoice_date_list.append(rec.invoice_date_due)
            invoice_date_list.sort()
            if invoice_date_list:
                self.invoice_date_due = invoice_date_list[0]

    def action_confirm(self):
        res = super(SaleOrder, self).action_confirm()
        self._get_date_due()
        err = 'Sorry you can not confirm sale order! This customer credit amount is more than limit. ' \
              'Please contact to your manager.'
        err1 = 'Sorry you can not confirm sale order! This customer credit due date is over. Please contact to ' \
               'your manager. '
        if not self.env.user.has_group('ax_base_setup.group_allow_credit_limit'):
            if self.over_credit is True and self.credit_limit < (self.amount_total + self.total_due):
                raise exceptions.ValidationError(err)
        if not self.env.user.has_group('ax_base_setup.group_allow_due'):
            if self.invoice_date_due and self.invoice_date_due <= self.sale_date and self.over_payment:
                raise exceptions.ValidationError(err1)
        return res


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    is_foc = fields.Boolean('FOC')
    price_unit = fields.Float('Unit Price', required=False, digits='Product Price', default=0.0)

    @api.onchange('is_foc')
    def onchange_is_foc(self):
        if self.is_foc:
            self.price_unit = 0
            self.price_subtotal = 0
        else:
            self._compute_amount()

    @api.model_create_multi
    def create(self, vals_list):
        lines = super(SaleOrderLine, self).create(vals_list)
        lines.overwrite_price_unit_of_foc_line()
        return lines

    def write(self, values):
        res = super(SaleOrderLine, self).write(values)
        self.overwrite_price_unit_of_foc_line()
        return res

    def overwrite_price_unit_of_foc_line(self):
        for line in self:
            if line.is_foc and line.price_unit != 0:
                line.price_unit = 0
