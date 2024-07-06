from odoo import models, fields, api, _


class Partner(models.Model):
    _inherit = "res.partner"

    partner_class_id = fields.Many2one('partner.class', string='Customer Class')
    payment_type = fields.Selection([('cash', 'Cash'),
                                     ('partial', 'Partial'),
                                     ('credit', 'Credit')], 'Payment Type', default='cash')