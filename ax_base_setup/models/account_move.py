from odoo import api, fields, models, exceptions, _
from odoo.exceptions import UserError, ValidationError, RedirectWarning, AccessError, Warning
import warnings


class AccountMove(models.Model):

    _inherit = "account.move"

    v_over_credit = fields.Boolean('Disallow Credit Limit', related='partner_id.v_over_credit')
    sale_credit_limit = fields.Float('Credit Limit', related='partner_id.credit_limit')
    purchase_credit_limit = fields.Float('Purchase Credit Limit', related='partner_id.v_credit_limit')
    total_due = fields.Monetary('Total Due Amount', readonly=True)

    @api.onchange('move_type')
    def onchange_type_domain(self):
        type = self.move_type
        if type in ['out_invoice', 'out_refund', 'out_receipt']:
            return {'domain': {'partner_id': [('customer', '=', True)]}}
        elif type in ['in_invoice', 'in_refund', 'in_receipt']:
            return {'domain': {'partner_id': [('supplier', '=', True)]}}

    def _stock_account_prepare_anglo_saxon_out_lines_vals(self):
        ''' Prepare values used to create the journal items (account.move.line) corresponding to the Cost of Good Sold
        lines (COGS) for customer invoices.

        Example:

        Buy a product having a cost of 9 being a storable product and having a perpetual valuation in FIFO.
        Sell this product at a price of 10. The customer invoice's journal entries looks like:

        Account                                     | Debit | Credit
        ---------------------------------------------------------------
        200000 Product Sales                        |       | 10.0
        ---------------------------------------------------------------
        101200 Account Receivable                   | 10.0  |
        ---------------------------------------------------------------

        This method computes values used to make two additional journal items:

        ---------------------------------------------------------------
        220000 Expenses                             | 9.0   |
        ---------------------------------------------------------------
        101130 Stock Interim Account (Delivered)    |       | 9.0
        ---------------------------------------------------------------

        Note: COGS are only generated for customer invoices except refund made to cancel an invoice.

        :return: A list of Python dictionary to be passed to env['account.move.line'].create.
        '''
        lines_vals_list = []
        for move in self:
            # Make the loop multi-company safe when accessing models like product.product
            move = move.with_company(move.company_id)

            if not move.is_sale_document(include_receipts=True) or not move.company_id.anglo_saxon_accounting:
                continue

            for line in move.invoice_line_ids:

                # Filter out lines being not eligible for COGS.
                if not line._eligible_for_cogs():
                    continue

                # Retrieve accounts needed to generate the COGS.
                accounts = line.product_id.product_tmpl_id.get_product_accounts(fiscal_pos=move.fiscal_position_id)
                debit_interim_account = accounts['stock_output']
                credit_expense_account = accounts['expense'] or self.journal_id.default_account_id
                if not debit_interim_account or not credit_expense_account:
                    continue

                if line.is_foc:
                    credit_expense_account = self.company_id.foc_discount_account_id
                    if not credit_expense_account:
                        raise UserError(_('Please configure FOC Discount Account!'))
                else:
                    credit_expense_account = accounts['expense']

                # Compute accounting fields.
                sign = -1 if move.move_type == 'out_refund' else 1
                price_unit = line._stock_account_get_anglo_saxon_price_unit()
                balance = sign * line.quantity * price_unit

                # Add interim account line.
                lines_vals_list.append({
                    'name': line.name[:64],
                    'move_id': move.id,
                    'product_id': line.product_id.id,
                    'product_uom_id': line.product_uom_id.id,
                    'quantity': line.quantity,
                    'price_unit': price_unit,
                    'debit': balance < 0.0 and -balance or 0.0,
                    'credit': balance > 0.0 and balance or 0.0,
                    'account_id': debit_interim_account.id,
                    'exclude_from_invoice_tab': True,
                    'is_anglo_saxon_line': True,
                })

                # Add expense account line.
                lines_vals_list.append({
                    'name': line.name[:64],
                    'move_id': move.id,
                    'product_id': line.product_id.id,
                    'product_uom_id': line.product_uom_id.id,
                    'quantity': line.quantity,
                    'price_unit': -price_unit,
                    'debit': balance > 0.0 and balance or 0.0,
                    'credit': balance < 0.0 and -balance or 0.0,
                    'account_id': credit_expense_account.id,
                    'analytic_account_id': line.analytic_account_id.id,
                    'analytic_tag_ids': [(6, 0, line.analytic_tag_ids.ids)],
                    'exclude_from_invoice_tab': True,
                    'is_anglo_saxon_line': True,
                })
        return lines_vals_list

    def action_post(self):
        users = self.env['res.users'].search([('id', '!=', self.env.user.id)]) #
        email_list = [usr.partner_id.email for usr in users if usr.partner_id.email]
        result = ",".join(email_list)
        if self.total_due > 0:
            purchase_credit_limit = self.purchase_credit_limit + self.total_due
            amount_total = self.amount_total
        else:
            amount_total = self.amount_total + abs(self.total_due)
            purchase_credit_limit = self.purchase_credit_limit
        if self.v_over_credit is True and purchase_credit_limit < amount_total:
            template_id = self.env['ir.model.data']._xmlid_lookup('ax_base_setup.email_template_edi_bill_credit_limit')[2]
            email_template_obj = self.env['mail.template'].browse(template_id)
            if email_template_obj:
                data = {'email_to': result}
                values = email_template_obj.with_context(data).generate_email(self.id,
                                                                              ['subject', 'body_html',
                                                                               'email_from', 'email_to',
                                                                               'partner_to', 'email_cc',
                                                                               'reply_to', 'scheduled_date'])
                values['email_to'] = result
                self.env['mail.mail'].create(values).send()
        return super(AccountMove, self).action_post()

    @api.model_create_multi
    def create(self, vals_list):
        res = super(AccountMove, self).create(vals_list)
        if self.move_type in ('in_invoice', 'in_refund', 'in_receipt'):
            if self.total_due > 0:
                purchase_credit_limit = self.purchase_credit_limit + self.total_due
                amount_total = self.amount_total
            else:
                amount_total = self.amount_total + abs(self.total_due)
                purchase_credit_limit = self.purchase_credit_limit
            if self.v_over_credit is True and purchase_credit_limit < amount_total:
                return {
                    'warning': {
                        'title': _('Warning!'),
                        'message': _("This supplier credit amount is more than limit.")}}
        return res


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    is_foc = fields.Boolean("FOC", related="sale_line_ids.is_foc", store=True)
