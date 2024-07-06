from odoo import api, fields, models
from odoo.addons.base.models.res_partner import WARNING_MESSAGE, WARNING_HELP

class ResPartner(models.Model):
    _inherit = 'res.partner'

    # For PO Register Payment Button Warning Message 26 Oct 2022 MPP
    register_warn = fields.Selection([
        ('no-message', 'No Message'),
        ('warning', 'Alert')],
        'Vendor Bill & Register Payment',
        default="no-message")
    register_warn_msg = fields.Text('Alert Message for Vendor Bill & Register Payment')
    # For PO Register Payment Button Warning Message 26 Oct 2022 MPP

    purchaser_id = fields.Many2one(
        'res.users',
        string="Purchaser",
        copy=False,
    )  # Adding Purchaser By ETK
    purchaser_id_name = fields.Char(
        related = 'purchaser_id.name',
        copy=False,
        tracking = True
    )  # Adding Purchaser By AMM  # To disable auto mailing when user is changed

