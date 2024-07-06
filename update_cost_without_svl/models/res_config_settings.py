from odoo import api, models, fields


class ResConfigSettings(models.TransientModel):

    _inherit = 'res.config.settings'

    group_update_cost_without_svl = fields.Boolean("Update Cost Without SVL", implied_group='update_cost_without_svl.group_update_cost_without_svl')
