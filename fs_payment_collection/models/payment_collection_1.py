from odoo import api, models, fields, SUPERUSER_ID
from odoo import api, models, fields, SUPERUSER_ID
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from odoo.exceptions import ValidationError


class PaymentCollectionOne(models.Model):

    _name = 'payment.collection.one'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Payment Collection One'
    _order = "date desc"

    name = fields.Char('Name', default='Draft')
    partner_id = fields.Many2one('res.partner', 'Customer', domain=[('customer', '=', True)], required=1)
    sale_man_id = fields.Many2one('res.users', 'Cash Collector', domain=[('share', '=', False)], required=1)
    team_id = fields.Many2one('crm.team', 'Sales Team', required=1, domain=[('is_van_team', '=', True)])
    date = fields.Datetime('Assigned Date', default=fields.Datetime.now, required=1)
    to_collect_date = fields.Date('To Collect Date', required=1)
    

    to_collect_amt = fields.Monetary('To Collect Amount', currency_field='currency_id')
    collected_amt = fields.Monetary('Collected Amount', compute="_get_collect_amt", currency_field='currency_id')
    
    currency_id = fields.Many2one('res.currency', 'Currency', default=lambda self: self.env.company.currency_id)
    


    company_id = fields.Many2one('res.company', 'Company', required=1, default=lambda self: self.env.company.id)
    payment_ids = fields.One2many('payment.collection.one.payment.line', 'payment_collection_id', 'Payments')
    account_payment_ids = fields.One2many('account.payment', 'payment_collection_one_id', 'Account Payments')
    invoice_address_id = fields.Many2one('res.partner',string='Invoice Address',domain=[('type', '=', "invoice")]) 
    invoice_address = fields.Char(string="Receipt Department Adddress")
    daily_sale_summary_id = fields.Many2one('daily.sale.summary', 'Daily Sale Summary', store=True)
    

    signature = fields.Image('Signature', help='Signature received through the portal.', copy=False, attachment=True, max_width=1024, max_height=1024)
    signed_by = fields.Char('Signed By', help='Name of the person that signed the VO.', copy=False)
    signed_on = fields.Datetime('Signed On', help='Date of the signature.', copy=False)
    
    salesman_signature = fields.Image('Signature', help='Signature received through the portal.', copy=False, attachment=True, max_width=1024, max_height=1024)
    salesman_signed_by = fields.Char('Signed By', help='Name of the person that signed the VO.', copy=False)
    salesman_signed_on = fields.Datetime('Signed On', help='Date of the signature.', copy=False)
    
    mobile_ref = fields.Char('Mobile Reference')
    slip_image = fields.Image('Slip Image')
    state = fields.Selection([('draft', 'New'),
                              ('confirm', 'Confirmed'),
                              ('approve', 'Approved')], 'State', default='draft')

    @api.depends('payment_ids')
    def _get_collect_amt(self):

        total = 0
        for i in self:
            if i.payment_ids:
                for rec in i.payment_ids:
                    total += rec.amount
            i.collected_amt  = total



    @api.onchange('invoice_address_id')
    def onchange_invoice_address_id(self):
        for rec in self:
            invoice_address = ''
            if rec.invoice_address_id.street:
                invoice_address += rec.invoice_address_id.street + ", "
            if rec.invoice_address_id.street2:
                invoice_address += rec.invoice_address_id.street2 + ", "
            if rec.invoice_address_id.township_id:
                invoice_address += rec.invoice_address_id.township_id.name + ", "
            if rec.invoice_address_id.x_city_id:
                invoice_address += rec.invoice_address_id.x_city_id.name + ", "
            if rec.invoice_address_id.state_id:
                invoice_address += rec.invoice_address_id.state_id.name + ", "
            if rec.invoice_address_id.country_id:
                invoice_address += rec.invoice_address_id.country_id.name
            rec.invoice_address = invoice_address[:-1]

    @api.constrains('to_collect_date', 'partner_id', 'team_id')
    def _check_duplicate_record(self):
        for rec in self:
            duplicate = self.env['payment.collection'].search([('id', '!=', rec.id),
                                                               ('to_collect_date', '=', rec.to_collect_date),
                                                               ('partner_id', '=', rec.partner_id.id),
                                                               ('team_id', '=', rec.team_id.id)])
            if duplicate:
                raise ValidationError('Record with the same customer and sales team for the selected date already exists.')



    def btn_confirm(self):
        for payment in self:
            date = payment.date.date()
            payment.write({
                'name': self.env['ir.sequence'].sudo().next_by_code('pay.collection.seq', sequence_date=date),
                'state': 'confirm'
            })

    def _prepare_payment(self, payment):
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
            'analytic_account_id': self.team_id.analytic_account_id.id,
            'journal_id': payment.journal_id.id,
            'currency_id': payment.currency_id.id,
            'partner_id': self.partner_id.id,
            'payment_method_line_id': payment_method_line_id,
            'payment_collection_one_id': self.id,
        }

    def _create_payments(self):
        for payment in self.payment_ids:
            payment_vals = self._prepare_payment(payment)
            if not payment_vals:
                continue
            invoice_payment = self.env['account.payment'].with_user(SUPERUSER_ID).create(payment_vals)
            invoice_payment.action_post()

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
        for i in self:
            i.write({
                'state': 'approve'
            })

    def action_receive(self):
        for payment in self:
            payment._action_receive()


class PaymentCollectionOnePaymentLine(models.Model):

    _name = 'payment.collection.one.payment.line'
    _description = 'Payment Lines of Payment Collection'
    _rec_name = 'payment_collection_id'
    _order = "date desc"

    date = fields.Datetime('Date', default=fields.Datetime.now, required=True)
    payment_method_id = fields.Many2one('fieldsale.payment.method', 'Payment Method', required=True)
    journal_id = fields.Many2one('account.journal', 'Journal', related='payment_method_id.journal_id', store=True)
    amount = fields.Monetary('Amount', currency_field='currency_id', required=True)
    currency_id = fields.Many2one('res.currency', 'Currency', required=True)
    payment_collection_id = fields.Many2one('payment.collection.one', 'Payment Collection', ondelete='cascade', required=True)
    remark = fields.Text(string="Remark")
    partner_id = fields.Many2one(related="payment_collection_id.partner_id", string="Customer")
    daily_sale_summary_id = fields.Many2one(related="payment_collection_id.daily_sale_summary_id",string= 'Daily Sale Summary', store=True)
    
