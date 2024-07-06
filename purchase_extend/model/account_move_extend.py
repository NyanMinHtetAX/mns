from odoo import api, fields, models, _
from odoo.exceptions import Warning
from odoo.exceptions import ValidationError, UserError
import logging

_logger = logging.getLogger(__name__)

class AccountMove(models.Model):

    _inherit = 'account.move'
    # For PO Register Payment Button Warning Message 26 Oct 2022 MPP
    warning_message = fields.Text('Alert Message', compute='warning_message_payment')
    purchaser_id = fields.Many2one('res.users', string='Purchaser')

    @api.depends('partner_id')
    def warning_message_payment(self):
        self.warning_message = False
        if not self.partner_id or not self.env.user.has_group('purchase.group_warning_purchase'):
            return
        if self.move_type == 'in_invoice':
            partner = self.partner_id
            if partner.register_warn == 'warning':
                message = partner.register_warn_msg
                self.warning_message = message
            else:
                self.warning_message = ''
    # For PO Register Payment Button Warning Message 26 Oct 2022 MPP

