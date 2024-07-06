from odoo import models, fields, api, _


class ResPartner(models.Model):
    _inherit = 'res.partner'

    is_delivery_man = fields.Boolean(string='Delivery Man', default=False)
    vehicle_no = fields.Char(string='Vehicle Number')

    payment_type = fields.Selection([('cash', 'Cash'),
                                     ('partial', 'Partial'),
                                     ('credit', 'Credit')], 'Payment Type', default='cash')


