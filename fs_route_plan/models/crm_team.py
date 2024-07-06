from odoo import api, models, fields, _


class CrmTeam(models.Model):

    _inherit = 'crm.team'

    # route_plan_ids = fields.Many2many('route.plan', 'route_plan_sale_team_rel', 'sale_team_id', 'route_plan_id', 'Route Plans')
    route_plan_ids = fields.One2many('route.plan', 'sale_team_id', 'Route Plans')
