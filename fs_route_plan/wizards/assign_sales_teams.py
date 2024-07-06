from odoo import api, models, fields, _
from odoo.exceptions import UserError, ValidationError
from datetime import datetime

class AssignSalesTeams(models.TransientModel):

    _name = 'assign.sales.teams'
    _description = 'Assign Sales Teams'

    sale_team_id = fields.Many2one('crm.team', 'Sales Team', domain=[('is_van_team', '=', True)])
    route_plan_id = fields.Many2one('route.plan', 'Route Plan')

    def btn_assign(self):
        if self.sale_team_id:
            route_data = self.env['route.plan'].sudo().search(
                [('id', '!=', self.route_plan_id.id), ('sale_team_id', '!=', self.sale_team_id.id), ('weekday', '=', self.route_plan_id.weekday),('active','=',True)])
            week_data = self.env['route.plan'].sudo().search(
                [('id', '!=', self.route_plan_id.id), ('sale_team_id', '=', self.sale_team_id.id), ('weekday', '=', self.route_plan_id.weekday),('active','=',True)])
            if week_data:
                raise UserError(
                            "Current weekday is already existed in another route plan"
                        )
            member_list = []
            for rec in self.route_plan_id.partner_ids:
                for record in rec:
                    member_list.append(record.partner_id.id)

            for i in route_data.partner_ids:
                for record in i:
                    if record.partner_id.id in member_list:
                        raise UserError(
                            record.partner_id.name + " is already exist in other routes"
                        )
        
        self.route_plan_id.write({'sale_team_id': self.sale_team_id.id})
        self.sale_team_id.write({
            'write_date': datetime.now()
        })
        route_partner = []
        all_partner = []
        remaining_list = []
        route_data = self.env['route.plan'].sudo().search([('company_id','=',self.env.company.id)])
        for rec in route_data.partner_ids:
            route_partner.append(rec.id)
        partner_data = self.env['res.partner'].sudo().search([('customer','=',True),('company_id','=',self.env.company.id)])
        for rec in partner_data:
            all_partner.append(rec.id)
        remaining_list = [x.id for x in partner_data if x.id not in route_partner]
        
        if remaining_list:
            unassigned_customer_data = self.env['res.partner'].sudo().search([('id','in',remaining_list)])
            for rec in unassigned_customer_data:
                rec.write({
                        'is_route_plan': False
                        })
        for rec in self.route_plan_id.partner_ids:
            if rec.partner_id:
                rec.partner_id.write({
                    'write_date': datetime.now()
                    })
                rec.partner_id.write({
                    'is_route_plan': True
                    })

