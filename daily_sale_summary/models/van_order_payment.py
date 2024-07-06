from odoo import models, fields


class VanOrderPayment(models.Model):

    _name = 'van.order.payment'
    _description = 'Van Order Payment'

    date = fields.Datetime('Date', default=fields.Datetime.now, required=True)
    payment_method_id = fields.Many2one('fieldsale.payment.method', 'Payment Method', required=True)
    journal_id = fields.Many2one('account.journal', 'Journal', related='payment_method_id.journal_id', store=True)
    amount = fields.Monetary('Amount', currency_field='currency_id', required=True)
    currency_id = fields.Many2one('res.currency', 'Currency', required=True)
    order_id = fields.Many2one('van.order', 'Van Order', required=True, ondelete='cascade')
    daily_sale_summary_id = fields.Many2one('daily.sale.summary', 'Daily Sale Summary', related='order_id.daily_sale_summary_id', store=True)
