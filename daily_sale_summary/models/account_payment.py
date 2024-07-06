from odoo import api, models, fields


class AccountPayment(models.Model):

    _inherit = 'account.payment'

    van_order_id = fields.Many2one('van.order', 'Van Order')
