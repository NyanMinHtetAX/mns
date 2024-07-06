from odoo import api, models, fields
from odoo.exceptions import UserError
from datetime import datetime

class SaleTeamExtend(models.Model):

    _inherit = 'crm.team'
    _description = 'Sale Team Extend'

    use_quotations = fields.Boolean(default=True)
    use_opportunities = fields.Boolean(default=True)
    device_id = fields.Many2one('mobile.device', 'Device ID')
    vehicle_id = fields.Many2one('fleet.vehicle', 'Vehicle')
    products_count = fields.Integer("Products", compute="compute_products_count")
    route_plan_count = fields.Integer("Route Plan Count", compute="compute_route_plans_count")
    customers_count = fields.Integer("Customers", compute="compute_customers_count")
    partner_ids = fields.Many2many('res.partner', 'sale_team_partner_rel', 'partner_id', 'route_plan_id', compute="compute_customer_ids", store=True)
    picking_type_id = fields.Many2one('stock.picking.type',string="Operation Type")
    payment_method_ids = fields.Many2many('fieldsale.payment.method','sales_team_payment_methods','team_id','payment_id','Payment Methods')
    invoice_journal_id = fields.Many2one('account.journal','Invoice Journal')
    analytic_account_id = fields.Many2one('account.analytic.account','Analytic Account')
    van_location_id = fields.Many2one('stock.location', 'Van Location', domain=[('usage', '=', 'internal')])
    product_group_ids = fields.Many2many('product.group', string='Product Groups')
    allowed_location_ids = fields.Many2many('stock.location',
                                            'sales_team_allowed_location_rel',
                                            'team_id',
                                            'location_id',
                                            'Allowed Locations',
                                            domain=[('usage', '=', 'internal')])
    is_van_team = fields.Boolean('Is Van Sales Team?')

    @api.constrains("code")
    def check_sale_team_code(self):
        crm_data = self.env['crm.team'].sudo().search([('id','!=',self.id),('is_van_team','=',True)])
        for i in crm_data:
            if i.code == self.code:
                raise UserError(
                    "Sale team code cannot be same as "+i.name
                )

    @api.onchange("member_ids")
    def check_member_id(self):
        if self.is_van_team:
            crm_data = self.env['crm.team'].sudo().search([('id','!=',self._origin.id),('company_id','=',self.company_id.id),('is_van_team','=',True),('active','=',True)])
            member_list = []
            member_list_one = []
            for rec in self.member_ids.ids:
                member_list.append(rec)
            for i in crm_data:
                for rec in i.member_ids.ids:
                    member_list_one.append(rec)

            for i in crm_data:
                for b in i.member_ids:
                    if b.id in member_list:
                        raise UserError(
                            b.name+ " is already exist in other team"
                        )

    @api.constrains("van_location_id")
    def check_van_location_id(self):
        crm_data = self.env['crm.team'].sudo().search([('id','!=',self.id),('is_van_team','=',True)])
        
        for rec in crm_data:
            if rec.van_location_id.id == self.van_location_id.id:
                raise UserError(
                        "Current van location is already linked with " + rec.name
                    )

    @api.onchange('allowed_location_ids')
    def onchange_location_id(self):
        for rec in self:
            get_locations = self.env['stock.location'].search(
                [('id', '!=', rec.van_location_id.id), ('usage', '=', 'internal')])
            if rec.van_location_id:
                return {'domain': {'allowed_location_ids': [('id', 'in', get_locations.ids)]}}
            else:
                return {'domain': {'allowed_location_ids': []}}

    def compute_route_plans_count(self):
        if self.route_plan_ids:
            self.route_plan_count = len(self.route_plan_ids)
        else:
            self.route_plan_count = 0

    def action_view_route_plan(self):
        route_plan_ids = self.route_plan_ids
        return {
            'name': 'Route Plans',
            'type': 'ir.actions.act_window',
            'res_model': 'route.plan',
            'domain': [('id', 'in', route_plan_ids.ids)],
            'view_mode': 'tree,form',
        }

    @api.depends("route_plan_ids")
    def compute_customer_ids(self):
        partners = []
        for line in self.route_plan_ids:
            for partner in line.partner_ids:
                if partner.partner_id:
                    partners.append(partner.partner_id.id)
        self.partner_ids = [(6, 0, partners)]

    def compute_customers_count(self):
        if self.partner_ids:
            self.customers_count = len(self.partner_ids)
        else:
            self.customers_count = 0

    def action_view_customers(self):
        partner_ids = self.partner_ids
        return {
            'name': 'Customers',
            'type': 'ir.actions.act_window',
            'res_model': 'res.partner',
            'domain': [('id', 'in', partner_ids.ids)],
            'view_mode': 'tree,form',
        }

    def compute_products_count(self):
        for team in self:
            group_ids = team.product_group_ids
            products = self.env['product.product'].search([('product_group_id', 'in', group_ids.ids)])
            team.products_count = len(products)

    @api.onchange('product_group_ids')
    def onchang_product_group_ids(self):
        for team in self:
            group_ids = team.product_group_ids
            products = self.env['product.product'].search([('product_group_id', 'in', group_ids.ids)])
            
            products.write({
                'write_date': datetime.now()
            })

    def action_view_products(self):
        group_ids = self.product_group_ids
        return {
            'name': 'Products',
            'type': 'ir.actions.act_window',
            'res_model': 'product.product',
            'domain': [('product_group_id', 'in', group_ids.ids)],
            'view_mode': 'tree,form',
        }
