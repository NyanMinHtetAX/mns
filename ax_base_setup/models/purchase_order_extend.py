from odoo import models, fields, api, _, exceptions
from odoo import SUPERUSER_ID


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    credit_limit = fields.Float('Credit Limit Amount', related='partner_id.v_credit_limit')
    over_credit = fields.Boolean('Disallow Credit Limit', related='partner_id.v_over_credit')
    total_due = fields.Monetary('Total Due Amount', readonly=True, related='partner_id.amount_due')
    purchase_date = fields.Date('Date', required=True, readonly=False, default=fields.date.today())
    invoice_date_due = fields.Date('Invoice Due Date', readonly=True)
    over_payment = fields.Boolean('Unallow Payment', related='partner_id.v_over_payment')

    @api.onchange('partner_id')
    def _get_date_due(self):
        self.invoice_date_due = ''
        if self.partner_id and self.over_credit is True or self.over_payment is True:
            query = """ SELECT a.invoice_date_due as date FROM account_move a
                    WHERE a.partner_id is not null
                    AND a.move_type in ('in_invoice', 'in_receipt')
                    AND a.state = 'posted'
                    AND a.company_id='""" + str(self.company_id.id) +"""'
                    AND a.partner_id='""" + str(self.partner_id.id) \
                    + """' AND payment_state !='paid' ORDER BY invoice_date_due"""
            self.env.cr.execute(query)
            result = self.env.cr.dictfetchall()
            if result:
                self.invoice_date_due = result[0]['date']

    def button_confirm(self):
        self._get_date_due()
        res = super(PurchaseOrder, self).button_confirm()
        err = 'Sorry you can not confirm Purchase order! This Supplier credit amount is more than limit. ' \
              'Please contact to your manager.'
        err1 = 'Sorry you can not confirm sale order! This customer credit due date is over. Please contact to ' \
               'your manager. '
        if not self.env.user.has_group('ax_base_setup.group_allow_credit_limit'):
            if self.total_due > 0:
                credit_amount = self.credit_limit + self.total_due
                amount_total = self.amount_total
            else:
                amount_total = self.amount_total + abs(self.total_due)
                credit_amount = self.credit_limit
            if self.over_credit is True and credit_amount < amount_total:
                raise exceptions.ValidationError(err)
        if not self.env.user.has_group('ax_base_setup.group_allow_vendor_due'):
            if self.invoice_date_due and self.invoice_date_due <= self.purchase_date and self.over_payment:
                raise exceptions.ValidationError(err1)
        return res
