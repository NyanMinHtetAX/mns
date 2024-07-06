from odoo import api, models, fields


class AccountPayment(models.Model):

    _inherit = 'account.payment'

    payment_collection_id = fields.Many2one('payment.collection', 'Cash Collection')
    payment_collection_one_id = fields.Many2one('payment.collection.one', 'Payment Collection')
