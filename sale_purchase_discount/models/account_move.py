from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class AccountMove(models.Model):
    _inherit = "account.move"

    ks_global_discount_type = fields.Selection([
        ('percent', 'Percentage'),
        ('amount', 'Amount')],
        string='Global Discount Type',
        readonly=True,
        states={'draft': [('readonly', False)],
                'sent': [('readonly', False)]},
        default='percent')
    ks_global_discount_rate = fields.Float('Global Discount Rate',
                                           readonly=True,
                                           states={'draft': [('readonly', False)],
                                                   'sent': [('readonly', False)]})
    ks_amount_discount = fields.Monetary(string='Global Discount',
                                         readonly=True,
                                         compute='_compute_amount',
                                         store=True)
    ks_enable_discount = fields.Boolean(compute='ks_verify_discount')
    ks_sales_discount_account_id = fields.Integer(compute='ks_verify_discount')
    ks_purchase_discount_account_id = fields.Integer(compute='ks_verify_discount')

    @api.depends('company_id.ks_enable_discount')
    def ks_verify_discount(self):
        for rec in self:
            rec.ks_enable_discount = rec.company_id.ks_enable_discount
            rec.ks_sales_discount_account_id = rec.company_id.ks_sales_discount_account.id
            rec.ks_purchase_discount_account_id = rec.company_id.ks_purchase_discount_account.id

    @api.depends(
        'line_ids.debit',
        'line_ids.credit',
        'line_ids.currency_id',
        'line_ids.amount_currency',
        'line_ids.amount_residual',
        'line_ids.amount_residual_currency',
        'line_ids.payment_id.state',
        'ks_global_discount_type',
        'ks_global_discount_rate')
    def _compute_amount(self):
        super(AccountMove, self)._compute_amount()
        for rec in self:
            if not rec.asset_id:
                if not ('ks_global_tax_rate' in rec):
                    rec.ks_calculate_discount()
                sign = rec.move_type in ['in_refund', 'out_refund'] and -1 or 1
                rec.amount_total_signed = rec.amount_total * sign

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
                rec.ks_global_discount_rate = 0
                rec.ks_amount_discount = 0
            rec.amount_total = rec.amount_tax + rec.amount_untaxed - rec.ks_amount_discount
            rec.ks_update_universal_discount()

    @api.constrains('ks_global_discount_rate')
    def ks_check_discount_value(self):
        if self.ks_global_discount_type == "percent":
            if self.ks_global_discount_rate > 100 or self.ks_global_discount_rate < 0:
                raise ValidationError('You cannot enter percentage value greater than 100.')
        else:
            if self.ks_global_discount_rate < 0 or self.amount_untaxed < 0:
                raise ValidationError(
                    'You cannot enter discount amount greater than actual cost or value lower than 0.')

    @api.model
    def _prepare_refund(self, invoice, date_invoice=None, date=None, description=None, journal_id=None):
        ks_res = super(AccountMove, self)._prepare_refund(invoice, date_invoice=None, date=None,
                                                          description=None, journal_id=None)
        ks_res['ks_global_discount_rate'] = self.ks_global_discount_rate
        ks_res['ks_global_discount_type'] = self.ks_global_discount_type
        return ks_res

    def ks_update_universal_discount(self):
        """This Function Updates the Global Discount through Sale Order"""
        for rec in self:
            already_exists = self.line_ids.filtered(
                lambda line: line.name and line.name.find('Global Discount') == 0)
            terms_lines = self.line_ids.filtered(
                lambda line: line.account_id.user_type_id.type in ('receivable', 'payable'))
            other_lines = self.line_ids.filtered(
                lambda line: line.account_id.user_type_id.type not in ('receivable', 'payable'))

            different_currency = False
            if rec.currency_id != rec.company_id.currency_id:
                different_currency = True

            if already_exists:
                amount = rec.ks_amount_discount
                amount = rec.currency_id._convert(
                    amount, rec.company_id.currency_id, rec.company_id,
                    rec.date or fields.Date.today()
                )

                if rec.ks_sales_discount_account_id \
                        and (rec.move_type == "out_invoice"
                             or rec.move_type == "out_refund") \
                        and amount > 0:
                    if rec.move_type == "out_invoice":
                        already_exists.update({
                            'debit': amount > 0.0 and amount or 0.0,
                            'credit': amount < 0.0 and -amount or 0.0,
                        })
                    else:
                        already_exists.update({
                            'debit': amount < 0.0 and -amount or 0.0,
                            'credit': amount > 0.0 and amount or 0.0,
                        })
                    if different_currency:
                        if rec.move_type == "out_refund":
                            already_exists.update({
                                'amount_currency': -1 * rec.ks_amount_discount,
                                'currency_id': rec.currency_id.id
                            })
                        else:
                            already_exists.update({
                                'amount_currency': rec.ks_amount_discount,
                                'currency_id': rec.currency_id.id
                            })

                if rec.ks_purchase_discount_account_id \
                        and (rec.move_type == "in_invoice"
                             or rec.move_type == "in_refund") \
                        and amount > 0:
                    if rec.move_type == "in_invoice":
                        already_exists.update({
                            'debit': amount < 0.0 and -amount or 0.0,
                            'credit': amount > 0.0 and amount or 0.0,
                        })
                    else:
                        already_exists.update({
                            'debit': amount > 0.0 and amount or 0.0,
                            'credit': amount < 0.0 and -amount or 0.0,
                        })
                    if different_currency:
                        if rec.move_type == "in_refund":
                            already_exists.update({
                                'amount_currency': rec.ks_amount_discount,
                                'currency_id': rec.currency_id.id
                            })
                        else:
                            already_exists.update({
                                'amount_currency': -1 * rec.ks_amount_discount,
                                'currency_id': rec.currency_id.id
                            })
                total_balance = sum(other_lines.mapped('balance'))
                total_amount_currency = sum(other_lines.mapped('amount_currency'))
                terms_lines.update({
                    'amount_currency': -total_amount_currency,
                    'debit': total_balance < 0.0 and -total_balance or 0.0,
                    'credit': total_balance > 0.0 and total_balance or 0.0,
                })
            if not already_exists and rec.ks_global_discount_rate > 0:
                in_draft_mode = self != self._origin
                if not in_draft_mode and rec.move_type == 'out_invoice':
                    rec._recompute_universal_discount_lines()

    @api.onchange('ks_global_discount_rate', 'ks_global_discount_type', 'line_ids')
    def _recompute_universal_discount_lines(self):
        """This Function Create The General Entries for Global Discount"""
        for rec in self:

            different_currency = False
            if rec.currency_id != rec.company_id.currency_id:
                different_currency = True

            type_list = ['out_invoice', 'out_refund', 'in_invoice', 'in_refund']
            if rec.ks_global_discount_rate > 0 and rec.move_type in type_list:
                if rec.is_invoice(include_receipts=True):
                    in_draft_mode = self != self._origin
                    ks_name = "Global Discount "
                    if rec.ks_global_discount_type == "amount":
                        ks_value = "of amount #" + str(self.ks_global_discount_rate)
                    elif rec.ks_global_discount_type == "percent":
                        ks_value = " @" + str(self.ks_global_discount_rate) + "%"
                    else:
                        ks_value = ''
                    ks_name = ks_name + ks_value
                    #           ("Invoice No: " + str(self.ids)
                    #            if self._origin.id
                    #            else (self.display_name))
                    terms_lines = self.line_ids.filtered(
                        lambda line: line.account_id.user_type_id.type in ('receivable', 'payable'))
                    already_exists = self.line_ids.filtered(
                        lambda line: line.name and line.name.find('Global Discount') == 0)

                    if already_exists:
                        amount = self.ks_amount_discount
                        amount = rec.currency_id._convert(
                            amount, rec.company_id.currency_id, rec.company_id,
                            rec.date or fields.Date.today()
                        )

                        if self.ks_sales_discount_account_id \
                                and (self.move_type == "out_invoice"
                                     or self.move_type == "out_refund"):
                            if self.move_type == "out_invoice":
                                already_exists.update({
                                    'name': ks_name,
                                    'debit': amount > 0.0 and amount or 0.0,
                                    'credit': amount < 0.0 and -amount or 0.0,
                                })
                            else:
                                already_exists.update({
                                    'name': ks_name,
                                    'debit': amount < 0.0 and -amount or 0.0,
                                    'credit': amount > 0.0 and amount or 0.0,
                                })
                            if different_currency:
                                already_exists.update({
                                    'amount_currency': rec.ks_amount_discount,
                                    'currency_id': rec.currency_id.id
                                })

                        if self.ks_purchase_discount_account_id \
                                and (self.move_type == "in_invoice"
                                     or self.move_type == "in_refund"):
                            if self.move_type == "in_invoice":
                                already_exists.update({
                                    'name': ks_name,
                                    'debit': amount < 0.0 and -amount or 0.0,
                                    'credit': amount > 0.0 and amount or 0.0,
                                })
                                if different_currency:
                                    already_exists.update({
                                        'amount_currency': -1 * rec.ks_amount_discount,
                                        'currency_id': rec.currency_id.id
                                    })
                            else:
                                already_exists.update({
                                    'name': ks_name,
                                    'debit': amount > 0.0 and amount or 0.0,
                                    'credit': amount < 0.0 and -amount or 0.0,
                                })
                            if different_currency:
                                if rec.move_type == "in_refund":
                                    already_exists.update({
                                        'amount_currency': rec.ks_amount_discount,
                                        'currency_id': rec.currency_id.id
                                    })
                                else:
                                    already_exists.update({
                                        'amount_currency': -1 * rec.ks_amount_discount,
                                        'currency_id': rec.currency_id.id
                                    })

                    else:
                        new_tax_line = self.env['account.move.line']
                        create_method = in_draft_mode and \
                                        self.env['account.move.line'].new or \
                                        self.env['account.move.line'].create

                        if self.ks_sales_discount_account_id \
                                and (self.move_type == "out_invoice"
                                     or self.move_type == "out_refund"):
                            amount = self.ks_amount_discount
                            amount = rec.currency_id._convert(
                                amount, rec.company_id.currency_id, rec.company_id,
                                rec.date or fields.Date.today()
                            )
                            dict = {
                                'move_name': self.name,
                                'name': ks_name,
                                'price_unit': self.ks_amount_discount,
                                'quantity': 1,
                                'debit': amount < 0.0 and -amount or 0.0,
                                'credit': amount > 0.0 and amount or 0.0,
                                'account_id': self.ks_sales_discount_account_id,
                                'move_id': self._origin,
                                'date': self.date,
                                'exclude_from_invoice_tab': True,
                                'partner_id': terms_lines.partner_id.id,
                                'company_id': terms_lines.company_id.id,
                                'company_currency_id': terms_lines.company_currency_id.id,
                            }
                            if different_currency:
                                already_exists.update({
                                    'amount_currency': rec.ks_amount_discount,
                                    'currency_id': rec.currency_id.id
                                })

                            if self.move_type == "out_invoice":
                                dict.update({
                                    'debit': amount > 0.0 and amount or 0.0,
                                    'credit': amount < 0.0 and -amount or 0.0,
                                })
                            else:
                                dict.update({
                                    'debit': amount < 0.0 and -amount or 0.0,
                                    'credit': amount > 0.0 and amount or 0.0,
                                })
                            if in_draft_mode:
                                self.line_ids += create_method(dict)
                                # Updation of Invoice Line Id
                                duplicate_id = self.invoice_line_ids.filtered(
                                    lambda line: line.name and line.name.find('Global Discount') == 0)
                                self.invoice_line_ids = self.invoice_line_ids - duplicate_id
                            else:
                                dict.update({
                                    'price_unit': 0.0,
                                    'debit': 0.0,
                                    'credit': 0.0,
                                })
                                self.line_ids = [(0, 0, dict)]

                        if self.ks_purchase_discount_account_id \
                                and (self.move_type == "in_invoice"
                                     or self.move_type == "in_refund"):
                            amount = self.ks_amount_discount
                            amount = rec.currency_id._convert(
                                amount, rec.company_id.currency_id, rec.company_id,
                                rec.date or fields.Date.today()
                            )
                            dict = {
                                'move_name': self.name,
                                'name': ks_name,
                                'price_unit': self.ks_amount_discount,
                                'quantity': 1,
                                'debit': amount > 0.0 and amount or 0.0,
                                'credit': amount < 0.0 and -amount or 0.0,
                                'account_id': self.ks_purchase_discount_account_id,
                                'move_id': self.id,
                                'date': self.date,
                                'exclude_from_invoice_tab': True,
                                'partner_id': terms_lines.partner_id.id,
                                'company_id': terms_lines.company_id.id,
                                'company_currency_id': terms_lines.company_currency_id.id,
                            }

                            if different_currency:
                                dict.update({
                                    'amount_currency': -1 * rec.ks_amount_discount,
                                    'currency_id': rec.currency_id.id
                                })

                            if self.move_type == "in_invoice":
                                dict.update({
                                    'debit': amount < 0.0 and -amount or 0.0,
                                    'credit': amount > 0.0 and amount or 0.0,
                                })
                            else:
                                dict.update({
                                    'debit': amount > 0.0 and amount or 0.0,
                                    'credit': amount < 0.0 and -amount or 0.0,
                                })
                                if different_currency:
                                    dict.update({
                                        'amount_currency': rec.ks_amount_discount,
                                        'currency_id': rec.currency_id.id
                                    })
                            self.line_ids += create_method(dict)
                            # updation of invoice line id
                            duplicate_id = self.invoice_line_ids.filtered(
                                lambda line: line.name and line.name.find('Global Discount') == 0)
                            self.invoice_line_ids = self.invoice_line_ids - duplicate_id

                    if in_draft_mode:
                        # Update the payement account amount
                        terms_lines = self.line_ids.filtered(
                            lambda line: line.account_id.user_type_id.type in ('receivable', 'payable'))
                        other_lines = self.line_ids.filtered(
                            lambda line: line.account_id.user_type_id.type not in ('receivable', 'payable'))
                        total_balance = sum(other_lines.mapped('balance'))
                        total_amount_currency = sum(other_lines.mapped('amount_currency'))
                        terms_lines.update({
                            'amount_currency': -total_amount_currency,
                            'debit': total_balance < 0.0 and -total_balance or 0.0,
                            'credit': total_balance > 0.0 and total_balance or 0.0,
                        })
                    else:
                        terms_lines = self.line_ids.filtered(
                            lambda line: line.account_id.user_type_id.type in ('receivable', 'payable'))
                        other_lines = self.line_ids.filtered(
                            lambda line: line.account_id.user_type_id.type not in ('receivable', 'payable'))
                        already_exists = self.line_ids.filtered(
                            lambda line: line.name and line.name.find('Global Discount') == 0)
                        total_balance = sum(other_lines.mapped('balance')) + amount
                        total_amount_currency = sum(other_lines.mapped('amount_currency'))
                        dict1 = {
                            'debit': amount > 0.0 and amount or 0.0,
                            'credit': amount < 0.0 and -amount or 0.0,
                        }
                        dict2 = {
                            'debit': total_balance < 0.0 and -total_balance or 0.0,
                            'credit': total_balance > 0.0 and total_balance or 0.0,
                        }
                        self.line_ids = [(1, already_exists.id, dict1), (1, terms_lines.id, dict2)]
                        print()

            elif self.ks_global_discount_rate <= 0:
                already_exists = self.line_ids.filtered(
                    lambda line: line.name and line.name.find('Global Discount') == 0)
                if already_exists:
                    self.line_ids -= already_exists
                    terms_lines = self.line_ids.filtered(
                        lambda line: line.account_id.user_type_id.type in ('receivable', 'payable'))
                    other_lines = self.line_ids.filtered(
                        lambda line: line.account_id.user_type_id.type not in ('receivable', 'payable'))
                    total_balance = sum(other_lines.mapped('balance'))
                    total_amount_currency = sum(other_lines.mapped('amount_currency'))
                    terms_lines.update({
                        'amount_currency': -total_amount_currency,
                        'debit': total_balance < 0.0 and -total_balance or 0.0,
                        'credit': total_balance > 0.0 and total_balance or 0.0,
                    })

    def _recompute_dynamic_lines(self, recompute_all_taxes=False, recompute_tax_base_amount=False):
        ''' Recompute all lines that depend of others.

        For example, tax lines depends of base lines (lines having tax_ids set). This is also the case of cash rounding
        lines that depend of base lines or tax lines depending the cash rounding strategy. When a payment term is set,
        this method will auto-balance the move with payment term lines.

        :param recompute_all_taxes: Force the computation of taxes. If set to False, the computation will be done
                                    or not depending of the field 'recompute_tax_line' in lines.
        '''
        for invoice in self:
            # Dispatch lines and pre-compute some aggregated values like taxes.
            for line in invoice.line_ids:
                if line.recompute_tax_line:
                    recompute_all_taxes = True
                    line.recompute_tax_line = False

            # Compute taxes.
            if recompute_all_taxes:
                invoice._recompute_tax_lines()
            if recompute_tax_base_amount:
                invoice._recompute_tax_lines(recompute_tax_base_amount=True)

            if invoice.invoice_filter_type_domain == 'purchase':
                invoice._recompute_universal_discount_lines()

            if invoice.is_invoice(include_receipts=True):

                # Compute cash rounding.
                invoice._recompute_cash_rounding_lines()

                # Compute payment terms.
                invoice._recompute_payment_terms_lines()

                # Only synchronize one2many in onchange.
                if invoice != invoice._origin:
                    invoice.invoice_line_ids = invoice.line_ids.filtered(lambda line: not line.exclude_from_invoice_tab)

    def _recompute_tax_lines(self, recompute_tax_base_amount=False):
        ''' Compute the dynamic tax lines of the journal entry.

        :param lines_map: The line_ids dispatched by type containing:
            * base_lines: The lines having a tax_ids set.
            * tax_lines: The lines having a tax_line_id set.
            * terms_lines: The lines generated by the payment terms of the invoice.
            * rounding_lines: The cash rounding lines of the invoice.
        '''
        self.ensure_one()
        in_draft_mode = self != self._origin

        def _serialize_tax_grouping_key(grouping_dict):
            ''' Serialize the dictionary values to be used in the taxes_map.
            :param grouping_dict: The values returned by '_get_tax_grouping_key_from_tax_line' or '_get_tax_grouping_key_from_base_line'.
            :return: A string representing the values.
            '''
            return '-'.join(str(v) for v in grouping_dict.values())

        def _compute_base_line_taxes(base_line):
            ''' Compute taxes amounts both in company currency / foreign currency as the ratio between
            amount_currency & balance could not be the same as the expected currency rate.
            The 'amount_currency' value will be set on compute_all(...)['taxes'] in multi-currency.
            :param base_line:   The account.move.line owning the taxes.
            :return:            The result of the compute_all method.
            '''
            move = base_line.move_id

            if move.is_invoice(include_receipts=True):
                handle_price_include = True
                sign = -1 if move.is_inbound() else 1
                quantity = base_line.quantity
                is_refund = move.move_type in ('out_refund', 'in_refund')

                price_unit_foreign_curr = 0.0
                tax_type = 'sale' if move.move_type.startswith('out_') else 'purchase'
                if base_line.discount_type and base_line.discount_type == 'fixed':
                    if tax_type == 'sale':
                        price_unit_comp_curr = sign * base_line.price_unit + (
                                (base_line.discount * base_line.quantity) / (base_line.quantity or 1.0))
                    else:
                        price_unit_comp_curr = sign * base_line.price_unit - (
                                (base_line.discount * base_line.quantity) / (base_line.quantity or 1.0))
                else:
                    price_unit_comp_curr = sign * base_line.price_unit * (1 - (base_line.discount / 100.0))
                is_refund = move.move_type in ('out_refund', 'in_refund')
            else:
                handle_price_include = False
                quantity = 1.0
                price_unit_foreign_curr = base_line.amount_currency
                price_unit_comp_curr = base_line.balance
                tax_type = base_line.tax_ids[0].type_tax_use if base_line.tax_ids else None
                is_refund = (tax_type == 'sale' and base_line.debit) or (tax_type == 'purchase' and base_line.credit)

            balance_taxes_res = base_line.tax_ids._origin.with_context(
                force_sign=move._get_tax_force_sign()).compute_all(
                price_unit_comp_curr,
                currency=base_line.currency_id,
                quantity=quantity,
                product=base_line.product_id,
                partner=base_line.partner_id,
                is_refund=is_refund,
                handle_price_include=handle_price_include,
            )

            if move.move_type == 'entry':
                repartition_field = is_refund and 'refund_repartition_line_ids' or 'invoice_repartition_line_ids'
                repartition_tags = base_line.tax_ids.mapped(repartition_field).filtered(
                    lambda x: x.repartition_type == 'base').tag_ids
                tags_need_inversion = (tax_type == 'sale' and not is_refund) or (tax_type == 'purchase' and is_refund)
                if tags_need_inversion:
                    balance_taxes_res['base_tags'] = base_line._revert_signed_tags(repartition_tags).ids
                    for tax_res in balance_taxes_res['taxes']:
                        tax_res['tag_ids'] = base_line._revert_signed_tags(
                            self.env['account.account.tag'].browse(tax_res['tag_ids'])).ids

            if base_line.currency_id:
                # Multi-currencies mode: Taxes are computed both in company's currency / foreign currency.
                amount_currency_taxes_res = base_line.tax_ids._origin.with_context(
                    force_sign=move._get_tax_force_sign()).compute_all(
                    price_unit_foreign_curr,
                    currency=base_line.currency_id,
                    quantity=quantity,
                    product=base_line.product_id,
                    partner=base_line.partner_id,
                    is_refund=self.move_type in ('out_refund', 'in_refund'),
                    handle_price_include=handle_price_include,
                )

                if move.move_type == 'entry':
                    repartition_field = is_refund and 'refund_repartition_line_ids' or 'invoice_repartition_line_ids'
                    repartition_tags = base_line.tax_ids.mapped(repartition_field).filtered(
                        lambda x: x.repartition_type == 'base').tag_ids
                    tags_need_inversion = (tax_type == 'sale' and not is_refund) or (
                            tax_type == 'purchase' and is_refund)
                    if tags_need_inversion:
                        balance_taxes_res['base_tags'] = base_line._revert_signed_tags(repartition_tags).ids
                        for tax_res in balance_taxes_res['taxes']:
                            tax_res['tag_ids'] = base_line._revert_signed_tags(
                                self.env['account.account.tag'].browse(tax_res['tag_ids'])).ids

                for b_tax_res, ac_tax_res in zip(balance_taxes_res['taxes'], amount_currency_taxes_res['taxes']):
                    tax = self.env['account.tax'].browse(b_tax_res['id'])
                    b_tax_res['amount_currency'] = ac_tax_res['amount']

                    # A tax having a fixed amount must be converted into the company currency when dealing with a
                    # foreign currency.
                    if tax.amount_type == 'fixed':
                        b_tax_res['amount'] = base_line.currency_id._convert(b_tax_res['amount'],
                                                                             move.company_id.currency_id,
                                                                             move.company_id, move.date)
            return balance_taxes_res

        taxes_map = {}

        # ==== Add tax lines ====
        to_remove = self.env['account.move.line']
        for line in self.line_ids.filtered('tax_repartition_line_id'):
            grouping_dict = self._get_tax_grouping_key_from_tax_line(line)
            grouping_key = _serialize_tax_grouping_key(grouping_dict)
            if grouping_key in taxes_map:
                # A line with the same key does already exist, we only need one
                # to modify it; we have to drop this one.
                to_remove += line
            else:
                taxes_map[grouping_key] = {
                    'tax_line': line,
                    'amount': 0.0,
                    'tax_base_amount': 0.0,
                    'grouping_dict': False,
                }
        if not recompute_tax_base_amount:
            self.line_ids -= to_remove

        # ==== Mount base lines ====
        for line in self.line_ids.filtered(lambda line: not line.tax_repartition_line_id):
            # Don't call compute_all if there is no tax.
            if not line.tax_ids:
                if not recompute_tax_base_amount:
                    line.tax_tag_ids = [(5, 0, 0)]
                continue

            compute_all_vals = _compute_base_line_taxes(line)

            # Assign tags on base line
            if not recompute_tax_base_amount:
                line.tax_tag_ids = compute_all_vals['base_tags'] or [(5, 0, 0)]

            for tax_vals in compute_all_vals['taxes']:
                grouping_dict = self._get_tax_grouping_key_from_base_line(line, tax_vals)
                grouping_key = _serialize_tax_grouping_key(grouping_dict)

                tax_repartition_line = self.env['account.tax.repartition.line'].browse(
                    tax_vals['tax_repartition_line_id'])

                taxes_map_entry = taxes_map.setdefault(grouping_key, {
                    'tax_line': None,
                    'amount': 0.0,
                    'tax_base_amount': 0.0,
                    'grouping_dict': False,
                })
                taxes_map_entry['amount'] += tax_vals['amount']
                taxes_map_entry['tax_base_amount'] += self._get_base_amount_to_display(tax_vals['base'],
                                                                                       tax_repartition_line,
                                                                                       tax_vals['group'])
                taxes_map_entry['grouping_dict'] = grouping_dict

                # ==== Pre-process taxes_map ====
            taxes_map = self._preprocess_taxes_map(taxes_map)

            # ==== Process taxes_map ====
            for taxes_map_entry in taxes_map.values():
                # The tax line is no longer used in any base lines, drop it.
                if taxes_map_entry['tax_line'] and not taxes_map_entry['grouping_dict']:
                    if not recompute_tax_base_amount:
                        self.line_ids -= taxes_map_entry['tax_line']
                    continue

                currency = self.env['res.currency'].browse(taxes_map_entry['grouping_dict']['currency_id'])

                # Don't create tax lines with zero balance.
                if currency.is_zero(taxes_map_entry['amount']):
                    if taxes_map_entry['tax_line'] and not recompute_tax_base_amount:
                        self.line_ids -= taxes_map_entry['tax_line']
                    continue

                # tax_base_amount field is expressed using the company currency.
                tax_base_amount = currency._convert(taxes_map_entry['tax_base_amount'], self.company_currency_id,
                                                    self.company_id, self.date or fields.Date.context_today(self))

                # Recompute only the tax_base_amount.
                if recompute_tax_base_amount:
                    if taxes_map_entry['tax_line']:
                        taxes_map_entry['tax_line'].tax_base_amount = tax_base_amount
                    continue

                balance = currency._convert(
                    taxes_map_entry['amount'],
                    self.company_currency_id,
                    self.company_id,
                    self.date or fields.Date.context_today(self),
                )
                to_write_on_line = {
                    'amount_currency': taxes_map_entry['amount'],
                    'currency_id': taxes_map_entry['grouping_dict']['currency_id'],
                    'debit': balance > 0.0 and balance or 0.0,
                    'credit': balance < 0.0 and -balance or 0.0,
                    'tax_base_amount': tax_base_amount,
                }

                if taxes_map_entry['tax_line']:
                    # Update an existing tax line.
                    taxes_map_entry['tax_line'].update(to_write_on_line)
                else:
                    create_method = in_draft_mode and self.env['account.move.line'].new or self.env[
                        'account.move.line'].create
                    tax_repartition_line_id = taxes_map_entry['grouping_dict']['tax_repartition_line_id']
                    tax_repartition_line = self.env['account.tax.repartition.line'].browse(tax_repartition_line_id)
                    tax = tax_repartition_line.invoice_tax_id or tax_repartition_line.refund_tax_id
                    taxes_map_entry['tax_line'] = create_method({
                        **to_write_on_line,
                        'name': tax.name,
                        'move_id': self.id,
                        'partner_id': line.partner_id.id,
                        'company_id': line.company_id.id,
                        'company_currency_id': line.company_currency_id.id,
                        'tax_base_amount': tax_base_amount,
                        'exclude_from_invoice_tab': True,
                        **taxes_map_entry['grouping_dict'],
                    })

                if in_draft_mode:
                    taxes_map_entry['tax_line'].update(
                        taxes_map_entry['tax_line']._get_fields_onchange_balance(force_computation=True))


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    discount_type = fields.Selection(selection=[('percentage', 'Percentage'), ('fixed', 'Fixed')],
                                     string='Disc Type', default="fixed")
    discount = fields.Float(string="Dis/Refund")
    discount_amount = fields.Float(string="Dis Amt", compute='_get_discount_amount', store=True)

    @api.depends('price_unit', 'quantity', 'discount_type', 'discount')
    def _get_discount_amount(self):
        for record in self:
            if record.discount_type == 'percentage':
                discount_amt = record.price_unit * ((record.discount or 0.0) / 100.0) * record.quantity
            else:
                discount_amt = record.quantity * record.discount

            record.update({
                'discount_amount': discount_amt
            })

    @api.model
    def _get_price_total_and_subtotal_model(self, price_unit, quantity, discount, currency, product, partner, taxes,
                                            move_type):
        ''' This method is used to compute 'price_total' & 'price_subtotal'.

        :param price_unit:  The current price unit.
        :param quantity:    The current quantity.
        :param discount:    The current discount.
        :param currency:    The line's currency.
        :param product:     The line's product.
        :param partner:     The line's partner.
        :param taxes:       The applied taxes.
        :param move_type:   The type of the move.
        :return:            A dictionary containing 'price_subtotal' & 'price_total'.
        '''
        res = {}

        # Compute 'price_subtotal'.
        discount_type = ''
        if self._context and self._context.get('wk_vals_list', []):
            for vals in self._context.get('wk_vals_list', []):
                if price_unit == vals.get('price_unit', 0.0) and quantity == vals.get('quantity',
                                                                                      0.0) and discount == vals.get(
                        'discount', 0.0) and product.id == vals.get('product_id', False) and partner.id == vals.get(
                        'partner_id', False):
                    discount_type = vals.get('discount_type', '')
        discount_type = self.discount_type or discount_type or ''

        if discount_type == 'fixed':
            line_discount_price_unit = price_unit * quantity - (discount * quantity)
            quantity = 1.0
        else:
            line_discount_price_unit = price_unit * (1 - (discount / 100.0))
        subtotal = quantity * line_discount_price_unit

        # Compute 'price_total'.
        if taxes:
            force_sign = -1 if move_type in ('out_invoice', 'in_refund', 'out_receipt') else 1
            taxes_res = taxes._origin.with_context(force_sign=force_sign).compute_all(line_discount_price_unit,
                                                                                      quantity=quantity,
                                                                                      currency=currency,
                                                                                      product=product, partner=partner,
                                                                                      is_refund=move_type in (
                                                                                          'out_refund', 'in_refund'))
            res['price_subtotal'] = taxes_res['total_excluded']
            res['price_total'] = taxes_res['total_included']
        else:
            res['price_total'] = res['price_subtotal'] = subtotal

        # In case of multi currency, round before it's use for computing debit credit
        if currency:
            res = {k: currency.round(v) for k, v in res.items()}
        return res

    @api.model
    def _get_fields_onchange_balance_model(self, quantity, discount, amount_currency, move_type, currency, taxes,
                                           price_subtotal, force_computation=False):
        ''' This method is used to recompute the values of 'quantity', 'discount', 'price_unit' due to a change made
        in some accounting fields such as 'balance'.

        This method is a bit complex as we need to handle some special cases.
        For example, setting a positive balance with a 100% discount.

        :param quantity:        The current quantity.
        :param discount:        The current discount.
        :param balance:         The new balance.
        :param move_type:       The type of the move.
        :param currency:        The currency.
        :param taxes:           The applied taxes.
        :param price_subtotal:  The price_subtotal.
        :return:                A dictionary containing 'quantity', 'discount', 'price_unit'.
        '''
        balance_form = 'credit' if amount_currency > 0 else 'debit'
        if move_type in self.move_id.get_outbound_types():
            sign = 1
        elif move_type in self.move_id.get_inbound_types():
            sign = -1
        else:
            sign = 1
        amount_currency *= sign

        # Avoid rounding issue when dealing with price included taxes. For example, when the price_unit is 2300.0 and
        # a 5.5% price included tax is applied on it, a balance of 2300.0 / 1.055 = 2180.094 ~ 2180.09 is computed.
        # However, when triggering the inverse, 2180.09 + (2180.09 * 0.055) = 2180.09 + 119.90 = 2299.99 is computed.
        # To avoid that, set the price_subtotal at the balance if the difference between them looks like a rounding
        # issue.
        if not force_computation and currency.is_zero(amount_currency - price_subtotal):
            return {}

        taxes = taxes.flatten_taxes_hierarchy()
        if taxes and any(tax.price_include for tax in taxes):

            # Inverse taxes. E.g:
            #
            # Price Unit    | Taxes         | Originator Tax    |Price Subtotal     | Price Total
            # -----------------------------------------------------------------------------------
            # 110           | 10% incl, 5%  |                   | 100               | 115
            # 10            |               | 10% incl          | 10                | 10
            # 5             |               | 5%                | 5                 | 5
            #
            # When setting the balance to -200, the expected result is:
            #
            # Price Unit    | Taxes         | Originator Tax    |Price Subtotal     | Price Total
            # -----------------------------------------------------------------------------------
            # 220           | 10% incl, 5%  |                   | 200               | 230
            # 20            |               | 10% incl          | 20                | 20
            # 10            |               | 5%                | 10                | 10

            force_sign = -1 if move_type in ('out_invoice', 'in_refund', 'out_receipt') else 1
            taxes_res = taxes._origin.with_context(force_sign=force_sign).compute_all(amount_currency,
                                                                                      currency=currency,
                                                                                      handle_price_include=False)
            for tax_res in taxes_res['taxes']:
                tax = self.env['account.tax'].browse(tax_res['id'])
                if tax.price_include:
                    amount_currency += tax_res['amount']

        discount_type = ''
        if self._context and self._context.get('wk_vals_list', []):
            for vals in self._context.get('wk_vals_list', []):
                if quantity == vals.get('quantity', 0.0) and discount == vals.get('discount',
                                                                                  0.0) and amount_currency == vals.get(
                        balance_form, 0.0):
                    discount_type = vals.get('discount_type', '')
        discount_type = self.discount_type or discount_type or ''
        if discount_type == 'fixed':
            if amount_currency:
                vals = {
                    'quantity': quantity or 1.0,
                    'price_unit': (amount_currency + discount) / (quantity or 1.0),
                }
            else:
                vals = {'price_unit': 0.0}
        else:
            discount_factor = 1 - (discount / 100.0)
            if amount_currency and discount_factor:
                # discount != 100%
                vals = {
                    'quantity': quantity or 1.0,
                    'price_unit': amount_currency / discount_factor / (quantity or 1.0),
                }
            elif amount_currency and not discount_factor:
                # discount == 100%
                vals = {
                    'quantity': quantity or 1.0,
                    'discount': 0.0,
                    'price_unit': amount_currency / (quantity or 1.0),
                }
            elif not discount_factor:
                # balance of line is 0, but discount  == 100% so we display the normal unit_price
                vals = {}
            else:
                # balance is 0, so unit price is 0 as well
                vals = {'price_unit': 0.0}
        return vals

    @api.onchange('quantity', 'discount', 'discount_type', 'price_unit', 'tax_ids')
    def _onchange_price_subtotal(self):
        return super(AccountMoveLine, self)._onchange_price_subtotal()

    @api.model_create_multi
    def create(self, vals_list):
        context = self._context.copy()
        context.update({'wk_vals_list': vals_list})
        res = super(AccountMoveLine, self.with_context(context)).create(vals_list)
        return res
