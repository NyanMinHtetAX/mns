import logging
from math import ceil
from odoo import api, models, fields, _
from odoo.exceptions import UserError
_logger = logging.getLogger(__name__)

WEEK_XML_IDS = {
    1: 'fs_route_plan.week_one',
    2: 'fs_route_plan.week_two',
    3: 'fs_route_plan.week_three',
    4: 'fs_route_plan.week_four',
    5: 'fs_route_plan.week_five',
    6: 'fs_route_plan.week_six',
}


class RoutePlan(models.Model):
    _name = 'route.plan'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Route Plan'
    _order = "write_date desc"

    name = fields.Char('Name')
    code = fields.Char('Code')
    plan_type = fields.Selection([('day', 'Day Plan'),
                                  ('week', 'Week Plan'),
                                  ('trip', 'Trip Plan')], 'Plan Type')
    based_on = fields.Selection([('township', 'Township'),
                                 ('sale_channel', 'Channel'),
                                 ('outlet', 'Outlet'),
                                 ('custom', 'Custom')], 'Based On')
    township_ids = fields.Many2many('res.township', 'route_plan_township_rel', 'wp_id', 'township_id', 'Township')
    channel_ids = fields.Many2many('res.sale.channel', 'route_plan_channel_rel', 'wp_id', 'channel_id', 'Channel')
    outlet_ids = fields.Many2many('res.partner.outlet', 'route_plan_outlet_rel', 'wp_id', 'outlet_id', 'Outlet Type')
    week_id = fields.Selection([('w1', 'Week 1'),
                                ('w2', 'Week 2'),
                                ('w3', 'Week 3'),
                                ('w4', 'Week 4'),
                                ('w5', 'Week 5')], 'Week')
    weekday = fields.Selection([('Monday', 'Mon'),
                                ('Tuesday', 'Tue'),
                                ('Wednesday', 'Wed'),
                                ('Thursday', 'Thur'),
                                ('Friday', 'Fri'),
                                ('Saturday', 'Sat'),
                                ('Sunday', 'Sun')], 'Day', compute=None, store=True)
    begin_partner_id = fields.Many2one('res.partner', 'Begin Point')
    begin_partner_lat = fields.Float('Begin Lat', related='begin_partner_id.latitude', digits=(24, 12))
    begin_partner_lng = fields.Float('Begin Lng', related='begin_partner_id.longitude', digits=(24, 12))
    end_partner_id = fields.Many2one('res.partner', 'End Point')
    end_partner_lat = fields.Float('End Lat', related='end_partner_id.latitude', digits=(24, 12))
    end_partner_lng = fields.Float('End Lng', related='end_partner_id.longitude', digits=(24, 12))
    partner_ids = fields.One2many('route.plan.custom', 'route_plan_id')
    sale_team_id = fields.Many2one('crm.team', 'Sale Team')
    state = fields.Selection([('draft', 'Draft'),
                              ('confirm', 'Confirmed')], default='draft')
    start_date = fields.Date(string="Start Date")
    end_date = fields.Date(string="End Date")
    partner_count = fields.Integer('Partner Count', compute='_compute_partner_count', store=True)
    company_id = fields.Many2one('res.company', 'Company', default=lambda self: self.env.company.id, required=1)
    map_widget = fields.Char('Map Widget')
    active = fields.Boolean('Active', default=True)
    route_plan_date = fields.Date('Route Plan Date')

    @api.onchange('route_plan_date')
    def onchange_route_plan_date(self):
        if self.route_plan_date:
            self.write({
                "weekday": self.route_plan_date.strftime("%A")
            })

    @api.constrains('code')
    def check_code(self):
        crm_data = self.env['crm.team'].sudo().search([('is_van_team','=',True),('code','=',self.code)])
        if crm_data:
            raise UserError(
                            "Current route code is already exist in another route"
                        )

    @api.depends("partner_ids")
    def _compute_partner_count(self):
        count = 0
        for line in self.partner_ids:
            count += 1
        self.partner_count = count

    @api.onchange('begin_partner_id', 'end_partner_id')
    def onchange_start_point(self):
        self.partner_ids = [(5, False, False)]
        if self.begin_partner_id:
            self.partner_ids = [(4, self.begin_partner_id.id)]
        if self.end_partner_id:
            self.partner_ids = [(4, self.end_partner_id.id)]

    @api.onchange('based_on', 'township_ids', 'channel_ids', 'outlet_ids')
    def _auto_complete_customers(self):
        company = 'company'
        partners = self.env['res.partner'].sudo().search([('customer', '=', True), ('company_type', '=', 'company'), ('company_id','=',self.env.company.id),('active','=',True)])
        based_on = self.based_on
        townships = self.township_ids
        channels = self.channel_ids
        outlets = self.outlet_ids
        if based_on == 'township' and townships:
            partners = self.env['res.partner'].search([('township_id', 'in', townships.ids), ('customer', '=', True), ('company_type', '=', 'company'), ('company_id','=',self.env.company.id),('active','=',True)])
        elif based_on == 'sale_channel' and channels:
            partners = self.env['res.partner'].search(
                [('sale_channel_ids', 'in', channels.ids), ('customer', '=', True), ('company_type', '=', 'company'), ('company_id','=',self.env.company.id),('active','=',True)])
        elif based_on == 'outlet' and outlets:
            partners = self.env['res.partner'].search(
                [('outlet_type', 'in', townships.ids), ('customer', '=', True), ('company_type', '=', 'company'), ('company_id','=', self.env.company.id),('active','=',True)])
        self.partner_ids = [(5,False, False)]
        for rec in partners:
            self.partner_ids = [(0,0,{
                'partner_id': rec
                })]
        if partners:
            for i in partners:
                i.update({
                    "is_route_plan": True,
                })

    def btn_confirm(self):
        for rec in self:
            rec.write({'state': 'confirm'})


    def remove_all(self):
        check_in_data = self.env['route.plan.checkin'].sudo().search([('route_plan_id','=',self.id),('check_in','=',True)])
        if check_in_data:
            raise UserError('You cannot delete customer since they are already checkin')
        for rec in self.partner_ids:
            rec.partner_id.is_route_plan = False
        self.partner_ids = [(5,)]


    def open_web_view(self):
        current_model_id = self.env.context.get('active_id')
        return {
            'type': 'ir.actions.client',
            'name': 'Route Web View',
            'tag': 'RouteWebView',
            'context': {
                'active_id': self.id,
            }
        }

    @api.model
    def get_data(self, options):
        query = f"""
        select row_number() OVER (ORDER BY a.route_plan_id),b.name as name,b.ref as ref,b.phone as phone,outlet.name as outlet,TOWNSHIP.name as township,b.latitude as lat,b.longitude as long, a.* 
        from route_plan_partner_rel a
        left join res_partner b on b.id = a.partner_id
        left join res_township township on township.id = b.township_id
        left join res_partner_outlet outlet on outlet.id = b.outlet_type
where a.route_plan_id = {options['context']['context']['active_id']};
        """
        _logger.info(f'\n\n\nExecuting the query for top selling report------\n')
        _logger.info(f'\n{query}\n')
        self.env.cr.execute(query)
        records = self.env.cr.dictfetchall()
        return {
            'options': options,
            'records': records,
        }


    def action_view_partners(self):
        partner_list = []
        partners =  self.partner_ids
        for record in partners:
            partner_list.append(record.partner_id.id)
        view_id = self.env.ref('fs_route_plan.route_customer_map_view').id
        return {
            'name': 'Customers',
            'type': 'ir.actions.act_window',
            'res_model': 'res.partner',
            'domain': [('id', 'in', partner_list)],
            'view_mode': 'tree,form,map',
        }

    def action_view_route_plan_map(self):
        partner_list = []
        partners =  self.partner_ids
        for record in partners:
            partner_list.append(record.partner_id.id)
        view_id = self.env.ref('fs_route_plan.route_customer_map_view').id
        return {
            'name': 'Customers',
            'type': 'ir.actions.act_window',
            'res_model': 'res.partner',
            'domain': [('id', 'in', partner_list)],
            'view_mode': 'map',
            'views': [
                [(view_id), 'map']
            ]
        }

    def unlink(self):
        for route in self:
            if route.state != 'draft':
                raise UserError('You can only delete draft route plans.')
        return super(RoutePlan, self).unlink()

class RoutePlanSequence(models.Model):

    _name = 'route.plan.custom'
    _description = 'Route Plan Customer Sequence'
    _order = 'sequence,id'

    route_plan_id = fields.Many2one('route.plan')
    sequence = fields.Integer(default=10, index=True)
    partner_id = fields.Many2one('res.partner', string='Partners')
    ref = fields.Char(related='partner_id.ref')
    phone = fields.Char(related='partner_id.phone')
    sale_channel_ids = fields.Many2many(related='partner_id.sale_channel_ids')
    outlet_type = fields.Many2one(related='partner_id.outlet_type')
    company_id = fields.Many2one('res.company', compute="get_default_company")
    township_id = fields.Many2one(related='partner_id.township_id')
    latitude = fields.Float(related='partner_id.latitude')
    longitude = fields.Float(related='partner_id.longitude')
    check_in = fields.Boolean(compute="get_check_in", string="Check In")

    @api.model
    def get_default_company(self):
        self.company_id = self.env.company.id

    @api.depends('route_plan_id')
    def get_check_in(self):
        route_plan_data = self.env['route.plan.checkin'].sudo().search([('route_plan_id','=',self.route_plan_id.id)])
        if route_plan_data:
            self.check_in = route_plan_data.check_in
        else:
            self.check_in = False

    def unlink(self):
        self.ensure_one()
        check_in_data = self.env['route.plan.checkin'].sudo().search([('route_plan_id','=',self.route_plan_id.id),('check_in','=',True)])
        if check_in_data:
            raise UserError('You can only delete customer since they are already checkin')
        
        return super(RoutePlanSequence, self).unlink()



class RoutePlanCheckIn(models.Model):

    _name = 'route.plan.checkin'
    _description = 'Route Plan Check In'
    _order = 'id'

    route_plan_id = fields.Many2one('route.plan')
    sale_team_id = fields.Many2one('crm.team')
    day = fields.Char('day')
    date = fields.Date('date')
    check_in = fields.Boolean('Check In', default=False)
    
