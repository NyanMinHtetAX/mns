from odoo import api, models, fields


class ReportPartnerLedger(models.AbstractModel):

    _inherit = "account.partner.ledger"

    # filter_analytic = True
