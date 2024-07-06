import logging
from odoo.exceptions import Warning
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError

_logger = logging.getLogger(__name__)

class AccountPaymentRegister(models.TransientModel):
    _inherit = 'account.payment.register'
    # For PO Register Payment Button Warning Message 26 Oct 2022 MPP
    register_warn = fields.Text('Alert Message', compute='register_warn_alert')

    @api.depends('partner_id')
    def register_warn_alert(self):
        self.register_warn = ''
        for wizard in self:
            if not wizard.partner_id or not wizard.env.user.has_group('purchase.group_warning_purchase'):
                return
            partner = wizard.partner_id
            if partner.register_warn == 'warning':
                message = partner.register_warn_msg
                wizard.register_warn = message
            else:
                wizard.register_warn = ''
    # For PO Register Payment Button Warning Message 26 Oct 2022 MPP
