# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.
##############################################################################

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from datetime import date,datetime,timedelta
from dateutil.relativedelta import relativedelta

class monthly_statement_line(models.Model):
	
	_name = 'monthly.statement.line'
	_description = "Monthly Statement Line"
	_order = 'invoice_date'
	
	
	company_id = fields.Many2one('res.company', string='Company')
	partner_id = fields.Many2one('res.partner', string='Customer')
	name = fields.Char('Name') 
	invoice_date = fields.Date('Invoice Date')
	invoice_date_due = fields.Date('Due Date')
	result = fields.Float("Balance")
	amount_total = fields.Float("Invoices/Debits")
	credit_amount = fields.Float("Payments/Credits")
	state = fields.Selection(selection=[
			('draft', 'Draft'), 
			('posted', 'Posted'),
			('cancel', 'Cancelled')
		], string='Status', required=True, readonly=True, copy=False, tracking=True,
		default='draft')
	invoice_id = fields.Many2one('account.move', string='Invoice')
	currency_id = fields.Many2one(related='invoice_id.currency_id')
	amount_total_signed = fields.Monetary(related='invoice_id.amount_total_signed', currency_field='currency_id',)
	amount_residual = fields.Monetary(related='invoice_id.amount_residual')
	amount_residual_signed = fields.Monetary(related='invoice_id.amount_residual_signed', currency_field='currency_id',)

	@classmethod
	def _valid_field_parameter(cls, field, name):
		if name == 'tracking':
			return True
		return super(monthly_statement_line, cls)._valid_field_parameter(field, name)

class weekly_statement_line(models.Model):
	_name = 'weekly.statement.line'
	_description = "Weekly Statement Line"
	_order = 'invoice_date'

	company_id = fields.Many2one('res.company', string='Company')
	partner_id = fields.Many2one('res.partner', string='Customer')
	name = fields.Char('Name')
	invoice_date = fields.Date('Invoice Date')
	invoice_date_due = fields.Date('Due Date')
	result = fields.Float("Balance")
	amount_total = fields.Float("Invoices/Debits")
	credit_amount = fields.Float("Payments/Credits")
	state = fields.Selection(selection=[
		('draft', 'Draft'),
		('posted', 'Posted'),
		('cancel', 'Cancelled')
	], string='Status', required=True, readonly=True, copy=False, tracking=True,
		default='draft')
	invoice_id = fields.Many2one('account.move', string='Invoice')
	currency_id = fields.Many2one(related='invoice_id.currency_id')
	amount_total_signed = fields.Monetary(related='invoice_id.amount_total_signed', currency_field='currency_id', )
	amount_residual = fields.Monetary(related='invoice_id.amount_residual')
	amount_residual_signed = fields.Monetary(related='invoice_id.amount_residual_signed',
											 currency_field='currency_id', )

	@classmethod
	def _valid_field_parameter(cls, field, name):
		if name == 'tracking':
			return True
		return super(weekly_statement_line, cls)._valid_field_parameter(field, name)