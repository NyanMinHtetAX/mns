from odoo import models, fields, api, _


class HrExpense(models.Model):
    _inherit = 'hr.expense'

    fleet_service_log_id = fields.Many2one('fleet.vehicle.log.services', string='Fleet Service')
