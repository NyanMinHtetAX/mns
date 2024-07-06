from odoo import models, fields, api, _


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    move_type = fields.Selection(related='move_id.move_type')
    product_type = fields.Selection(related='product_id.detailed_type')

