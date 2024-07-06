from odoo import models, fields


class SaleReturnPayment(models.Model):

    _name = 'sale.return.payment'
    _description = 'Sale Return Payment'
    _rec_name = 'journal_id'

    date = fields.Datetime('Date', default=fields.Datetime.now, required=True)
    payment_method_id = fields.Many2one('fieldsale.payment.method', 'Payment Method', required=True)
    journal_id = fields.Many2one('account.journal', 'Journal', related='payment_method_id.journal_id', store=True)
    amount = fields.Monetary('Amount', currency_field='currency_id', required=True)
    currency_id = fields.Many2one('res.currency', 'Currency', required=True)
    return_id = fields.Many2one('sale.stock.return', 'Sale Return', required=True, ondelete='cascade')
    daily_sale_summary_id = fields.Many2one('daily.sale.summary', 'Daily Sale Summary',store=True)
