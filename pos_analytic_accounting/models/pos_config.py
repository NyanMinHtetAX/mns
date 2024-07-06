from odoo import api, models, fields


class PosConfig(models.Model):

    _inherit = 'pos.config'

    analytic_account_id = fields.Many2one('account.analytic.account', 'Analytic Account')
