from odoo import api, models, fields


class Partner(models.Model):

    _inherit = 'res.partner'

    @api.model
    def create_from_ui(self, partner, team_id):
        partner['team_id'] = team_id
        partner_id = super(Partner, self).create_from_ui(partner)
        return partner_id
