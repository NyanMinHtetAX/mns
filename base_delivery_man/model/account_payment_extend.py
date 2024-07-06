from odoo import models, fields, api, _


class AccountPayment(models.Model):
    _inherit = 'account.payment'

    product_image_ids = fields.One2many('product.images', 'payment_id', string="Multi Images", limit=4,
                                        copy=True)
    

class AccountMove(models.Model):
    _inherit = 'account.move'

    payment_attachment_ids = fields.One2many('product.images', 'move_id', string="Multi-Images", limit=4,
                                        copy=True)
