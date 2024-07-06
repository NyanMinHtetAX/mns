from odoo import api, models, fields, SUPERUSER_ID
from odoo import api, models, fields, SUPERUSER_ID
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from odoo.exceptions import ValidationError


class PaymentCollection(models.Model):

    _name = 'payment.collection'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Payment Collection'
    _order = "date desc"
 
    name = fields.Char('Name', default='Draft')
    partner_id = fields.Many2one('res.partner', 'Customer', domain=[('customer', '=', True)], required=1)
    sale_man_id = fields.Many2one('res.users', 'Cash Collector', domain=[('share', '=', False)], required=1)
    team_id = fields.Many2one('crm.team', 'Sales Team', required=1, domain=[('is_van_team', '=', True)])
    date = fields.Datetime('Assigned Date', default=fields.Datetime.now, required=1)
    to_collect_date = fields.Date('To Collect Date', required=1)
    line_ids = fields.One2many('payment.collection.line', 'collection_id', 'Lines')
    company_id = fields.Many2one('res.company', 'Company', required=1, default=lambda self: self.env.company.id)
    payment_ids = fields.One2many('payment.collection.payment.line', 'payment_collection_id', 'Payments')
    account_payment_ids = fields.One2many('account.payment', 'payment_collection_id', 'Account Payments')
    signature = fields.Image('Signature', help='Signature received through the portal.', copy=False, attachment=True, max_width=1024, max_height=1024)
    signed_by = fields.Char('Signed By', help='Name of the person that signed the VO.', copy=False)
    signed_on = fields.Datetime('Signed On', help='Date of the signature.', copy=False)
    
    salesman_signature = fields.Image('Signature', help='Signature received through the portal.', copy=False, attachment=True, max_width=1024, max_height=1024)
    salesman_signed_by = fields.Char('Signed By', help='Name of the person that signed the VO.', copy=False)
    salesman_signed_on = fields.Datetime('Signed On', help='Date of the signature.', copy=False)
    
    slip_image = fields.Image('Slip Image')
    state = fields.Selection([('draft', 'New'),
                              ('confirm', 'Confirmed'),
                              ('approve', 'Approved')], 'State', default='draft')

    invoice_address_id = fields.Many2one('res.partner',string='Invoice Address',domain=[('type', '=', "invoice")]) 
    daily_sale_summary_id = fields.Many2one('daily.sale.summary', 'Daily Sale Summary', store=True)
    mobile_ref = fields.Char('Mobile Reference')

    @api.constrains('to_collect_date', 'partner_id', 'team_id')
    def _check_duplicate_record(self):
        for rec in self:
            duplicate = self.env['payment.collection'].search([('id', '!=', rec.id),
                                                               ('to_collect_date', '=', rec.to_collect_date),
                                                               ('partner_id', '=', rec.partner_id.id),
                                                               ('team_id', '=', rec.team_id.id)])
            if duplicate:
                raise ValidationError('Record with the same customer and sales team for the selected date already exists.')

    @api.constrains('line_ids')
    def _check_duplicate_invoice(self):
        for rec in self:
            lines = rec.line_ids
            for line in lines:
                duplicate = lines.filtered(lambda l: l.invoice_id.id == line.invoice_id.id and l.id != line.id)
                if duplicate:       
                    if duplicate.invoice_id.payment_state != "partial":
                        raise ValidationError(f'{line.invoice_id.name} is already assigned.')

    @api.onchange('partner_id')
    def onchange_partner_id(self):
        lines = []
        self.line_ids = False
        if self.partner_id:
            invoices = self.env['account.move'].search([('state', '=', 'posted'),
                                                        ('partner_id', '=', self.partner_id.id),
                                                        ('move_type', '=', 'out_invoice'),
                                                        ('payment_state', 'in', ['not_paid', 'partial'])])
            for invoice in invoices:
                lines.append(
                    (0, 0, {
                        'invoice_id': invoice.id,
                        'payment_state': invoice.payment_state,
                    })
                )
        self.line_ids = lines

    def btn_confirm(self):
        for payment in self:
            date = payment.date.date()
            payment.write({
                'name': self.env['ir.sequence'].sudo().next_by_code('cash.collection.seq', sequence_date=date),
                'state': 'confirm'
            })

    def _prepare_payment(self, payment, destination_account_id):
        available_payment_method_lines = payment.journal_id._get_available_payment_method_lines('inbound')
        if available_payment_method_lines:
            payment_method_line_id = available_payment_method_lines[0]._origin.id
        else:
            payment_method_line_id = False
        return {
            'date': payment.date,
            'amount': payment.amount,
            'payment_type': 'inbound',
            'partner_type': 'customer',
            'ref': self.name,
            'journal_id': payment.journal_id.id,
            'currency_id': payment.currency_id.id,
            'partner_id': self.partner_id.id,
            'payment_method_line_id': payment_method_line_id,
            'destination_account_id': destination_account_id.id,
            'payment_collection_id': self.id,
        }

    def _create_payments(self):
        receivable_domain = [('account_internal_type', '=', 'receivable'), ('reconciled', '=', False)]
        receivable_line = self.line_ids.invoice_id.line_ids.filtered_domain(receivable_domain)
        if receivable_line:
            destination_account_id = receivable_line.account_id
            destination_account_id.ensure_one()
            for payment in self.payment_ids:
                payment_vals = self._prepare_payment(payment, destination_account_id)
                if not payment_vals:
                    continue
                invoice_payment = self.env['account.payment'].with_user(SUPERUSER_ID).create(payment_vals)
                invoice_payment.action_post()
                invoice_payment.analytic_account_id = self.line_ids.invoice_id.analytic_account_id
                for payment in self.account_payment_ids:
                    payment.move_id.write({
                        'analytic_account_id': self.line_ids.invoice_id.analytic_account_id,
                    })
                    payment.move_id.line_ids.write({
                        'analytic_account_id': self.line_ids.invoice_id.analytic_account_id,
                    })

    def btn_approve(self):
        for payment in self:
            payment._create_payments()

    def btn_approve_real(self):
        partial_list = []
        payment_list = []
        payment_collect_data = self.env['payment.collection'].sudo().search([('date','>',self.date)])
        for pcd in payment_collect_data:
            for i in pcd.line_ids.invoice_id.ids:
                payment_list.append(i)
        for payment in self.line_ids:
            
            if payment.payment_state == "partial":
                partial_list.append(int(payment.invoice_id.id))
        
        for i in self:
            i.write({
                'state': 'approve'
            })

    def action_receive(self):
        for payment in self:
            payment._action_receive()


class PaymentCollectionLine(models.Model):

    _name = 'payment.collection.line'
    _description = 'Payment Collection Line'
    _order = 'due_date asc'

    invoice_id = fields.Many2one('account.move', 'Invoice No.', required=1)
    invoice_date = fields.Date('Invoice Date', related='invoice_id.invoice_date', store=True)
    due_date = fields.Date('Due Date', related='invoice_id.invoice_date_due', store=True)
    amount_total = fields.Monetary('Invoice Amount', currency_field='currency_id', related='invoice_id.amount_total', store=True)
    amount_residual = fields.Monetary('Due Amount', currency_field='currency_id', related='invoice_id.amount_residual', store=True)
    amount_last_paid = fields.Monetary('Last Paid Amount', currency_field='currency_id', compute='_compute_last_payment', store=True)
    last_payment_date = fields.Date('Last Payment Date', compute='_compute_last_payment', store=True)
    amount_paid = fields.Monetary('Paid Amount', currency_field='currency_id')
    currency_id = fields.Many2one('res.currency', 'Currency', related='invoice_id.currency_id', store=True)
    payment_state = fields.Selection([
        ('not_paid', 'Not Paid'),
        ('partial', 'Partial'),
        ('received', 'Paid'),
    ], 'Payment Status')
    collection_id = fields.Many2one('payment.collection', 'Payment Collection', ondelete='cascade', required=1)

    @api.onchange('invoice_id')
    def _onchange_invoice_id(self):
        self.payment_state = self.invoice_id.payment_state

    @api.depends('invoice_id')
    def _compute_last_payment(self):
        for line in self:
            move = line.invoice_id
            payments = self.env['account.payment'].search([], order='date desc').filtered(lambda payment: move.id in payment.reconciled_invoice_ids.ids)
            if payments:
                line.last_payment_date = payments[0].date
                if payments[0].currency_id != move.currency_id:
                    line.amount_last_paid = payments[0].currency_id._convert(payments[0].amount, move.currency_id, self.env.company, payments[0].date)
                else:
                    line.amount_last_paid = payments[0].amount

    def btn_apply_payment(self):
        for line in self:
            invoice = line.invoice_id
            receivable_line = invoice.line_ids.filtered_domain([('account_internal_type', '=', 'receivable'),
                                                                ('reconciled', '=', False)])
            account_payment_ids = line.collection_id.account_payment_ids
            payment_lines = account_payment_ids.line_ids.filtered_domain([('account_internal_type', '=', 'receivable'),
                                                                          ('reconciled', '=', False)])
            for account in payment_lines.account_id:
                (payment_lines + receivable_line).filtered_domain(
                    [('account_id', '=', account.id), ('reconciled', '=', False)]).reconcile()
            if invoice.currency_id.round(invoice.amount_residual) == 0:
                line.payment_state = 'received'
            elif invoice.amount_residual < invoice.amount_total:
                line.payment_state = 'partial'


class PaymentCollectionPaymentLine(models.Model):

    _name = 'payment.collection.payment.line'
    _description = 'Payment Lines of Payment Collection'
    _rec_name = 'payment_collection_id'
    _order = "date desc"

    date = fields.Datetime('Date', default=fields.Datetime.now, required=True)
    payment_method_id = fields.Many2one('fieldsale.payment.method', 'Payment Method', required=True)
    journal_id = fields.Many2one('account.journal', 'Journal', related='payment_method_id.journal_id', store=True)
    amount = fields.Monetary('Amount', currency_field='currency_id', required=True)
    currency_id = fields.Many2one('res.currency', 'Currency', required=True)
    payment_collection_id = fields.Many2one('payment.collection', 'Payment Collection', ondelete='cascade', required=True)
    partner_id = fields.Many2one(related="payment_collection_id.partner_id", string="Customer")
    daily_sale_summary_id = fields.Many2one(related="payment_collection_id.daily_sale_summary_id",string= 'Daily Sale Summary', store=True)
    