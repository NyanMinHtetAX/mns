from odoo import api, models, fields


class StockPicking(models.Model):

    _inherit = 'stock.picking'

    payment_term_id = fields.Many2one('account.payment.term', 'Payment Term')
