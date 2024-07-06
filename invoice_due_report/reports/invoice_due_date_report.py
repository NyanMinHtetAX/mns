import json
from odoo import models, fields, api, tools
from odoo.fields import Date
from datetime import timedelta


class InvoiceDue(models.Model):

    _name = "invoice.due.sql.view"
    _description = "Invoice Due Date"
    _rec_name = 'invoice_id'
    _auto = False

    invoice_id = fields.Many2one('account.move',string='Invoice No.')
    amj_id = fields.Many2one('account.move',string='Journal No.')
    partner_id = fields.Many2one('res.partner', string='Customer Name')
    sale_person_id = fields.Many2one('res.users', string='Sale Person Name')
    sale_team_id = fields.Many2one('crm.team', string="Sales Team")
    currency_id = fields.Many2one('res.currency', string='Currency')
    company_id = fields.Many2one('res.company', string="Company")
    invoice_date = fields.Date(string='Invoice Date')
    due_date = fields.Date(string='Due Date')
    paid_date = fields.Date(string='Paid Date')
    paid_amount = fields.Monetary(default=0, string='Paid Amount', currency_field='currency_id', compute="get_invoices_with_paid_amounts")
    total_amount = fields.Monetary(default=0, string='Total Amount', currency_field='currency_id')
    is_due_date_less_than_paid_date = fields.Boolean(
        string='Due Date < Paid Date',
        compute='_compute_due_date_less_than_paid_date',
        store=True,
        readonly=True,
        default=False,
    )

    
    def _compute_due_date_less_than_paid_date(self):
        for record in self:
            if record.due_date > record.paid_date:
                record.is_due_date_less_than_paid_date = False
            else:
                record.is_due_date_less_than_paid_date = True

    def get_invoices_with_paid_amounts(self):
        result = []
        for rec in self:
            paid_amount = 0
            result = rec.invoice_id.sudo()._get_reconciled_info_JSON_values()
            for payment in result:
                if rec.due_date > payment['date']: 
                    if rec.amj_id.ref:
                        if str(rec.amj_id.name) + ' ('+str(rec.amj_id.ref)+')' == payment['ref']:
                            paid_amount = payment['amount']
                    else:
                        if str(rec.amj_id.name) == payment['ref']:
                            paid_amount = payment['amount']
            rec.paid_amount = paid_amount

    def _select(self):
        return """
			SELECT ROW_NUMBER() OVER() AS ID, invoice_id,company_id, amj_id, partner_id,currency_id, sale_person_id, sale_team_id, invoice_date, due_date, paid_date,is_due_date_less_than_paid_date,paid_amount, total_amount
FROM (
SELECT  
            invoice.id AS invoice_id, 
            invoice.company_id AS company_id, 
            amj.id as amj_id,
            invoice.partner_id AS partner_id,
            invoice.currency_id AS currency_id,
            invoice.invoice_user_id AS sale_person_id,
            invoice.team_id AS sale_team_id,
            invoice.invoice_date AS invoice_date,
            invoice.invoice_date_due  AS due_date,
            amj.date  AS paid_date,
            False AS is_due_date_less_than_paid_date,
            0 AS paid_amount,
            invoice.amount_total AS total_amount
            FROM account_payment pay 
            LEFT JOIN account_move amj ON amj.id = pay.move_id
            JOIN account_move_line line ON line.move_id = amj.id
            JOIN account_partial_reconcile part ON
                part.debit_move_id = line.id
                OR
                part.credit_move_id = line.id
            JOIN account_move_line counterpart_line ON
                part.debit_move_id = counterpart_line.id
                OR
                part.credit_move_id = counterpart_line.id
            JOIN account_move invoice ON invoice.id = counterpart_line.move_id
            JOIN account_account account ON account.id = line.account_id
            WHERE account.internal_type IN ('receivable')
                AND line.id != counterpart_line.id
                AND invoice.move_type in ('out_invoice')
                AND amj.date is not null
                AND invoice.invoice_date_due is not null
                AND invoice.state = 'posted'
                AND amj.date < invoice.invoice_date_due
                AND invoice.company_id = amj.company_id
                GROUP BY pay.id, invoice.id, amj.id
            
            UNION DISTINCT
            
SELECT      
            invoice.id AS invoice_id, 
            invoice.company_id AS company_id, 
            amj.id as amj_id,
            invoice.partner_id AS partner_id,
            invoice.currency_id AS currency_id,
            invoice.invoice_user_id AS sale_person_id,
            invoice.team_id AS sale_team_id,
            invoice.invoice_date AS invoice_date,
            invoice.invoice_date_due  AS due_date,
            amj.date  AS paid_date,
            False AS is_due_date_less_than_paid_date,
            0 AS paid_amount,
            invoice.amount_total AS total_amount
            
            from account_move amj
            JOIN account_move_line line ON line.move_id = amj.id
            JOIN account_partial_reconcile part ON
                part.debit_move_id = line.id
                OR
                part.credit_move_id = line.id
            JOIN account_move_line counterpart_line ON
                part.debit_move_id = counterpart_line.id
                OR
                part.credit_move_id = counterpart_line.id
            JOIN account_move invoice ON invoice.id = counterpart_line.move_id
            JOIN account_account account ON account.id = line.account_id
            WHERE account.internal_type IN ('receivable')
                AND line.id != counterpart_line.id
                AND invoice.move_type in ('out_invoice')
                AND amj.date is not null
                AND invoice.invoice_date_due is not null
                AND invoice.state = 'posted'
                AND amj.date < invoice.invoice_date_due
                AND invoice.company_id = amj.company_id
                GROUP BY invoice.id, amj.id
) As sub_query
		"""

    def init(self):
        table = "invoice_due_sql_view"
        tools.drop_view_if_exists(self.env.cr, table)

        query = '''
			CREATE OR REPLACE VIEW %s AS (
				%s
			)
		''' % (table, self._select())
        
        self.env.cr.execute(query)
