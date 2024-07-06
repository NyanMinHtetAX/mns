from datetime import datetime
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from odoo import models, fields, api, _


class SelectPartners(models.TransientModel):
    _name = 'select.partners'
    _description = 'Select Partner'

    partner_ids = fields.Many2many('res.partner', string='Partners')
    company_id = fields.Many2one('res.company', 'Company',
                                 default=lambda self: self.env.company.id)   # tracking=True,

    def select_partners(self):
        for rec in self:
            route_plan_data = rec.env['route.plan'].browse(rec._context.get('active_id', False))
            for partner in rec.partner_ids:
                rec.env['route.plan.custom'].create({
                    'route_plan_id': route_plan_data.id,
                    'partner_id': partner.id,
                })



