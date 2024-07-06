from odoo import api, models, fields


class Partner(models.Model):

    _inherit = 'res.partner'

    route_plan_id = fields.Many2one('route.plan', 'Route Plan')
    is_route_plan = fields.Boolean('Has Route Plan', default=False)
    company_type = fields.Selection(string='Company Type', 
        selection=[('person', 'Individual'), ('company', 'Company')],
        compute='_compute_company_type', inverse='_write_company_type', store=True)

    def route_plan_boolean(self):
        contact_data = self.env['res.partner'].sudo().search([('company_id','=',self.env.company.id)])
        for i in contact_data:
            i.is_route_plan = False


