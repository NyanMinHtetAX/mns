from odoo import api, fields, models, _
from odoo.exceptions import UserError


class DailySaleSummary(models.Model):

    _name = "daily.sale.summary"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Daily Sale Summary"
    _order = "date desc"

    name = fields.Char("Reference", default="New")
    sales_man = fields.Many2one('res.users','Salesman')
    team_id = fields.Many2one('crm.team','Sale Team',required=True, domain=[('is_van_team', '=', True)])
    date = fields.Date("Date")
    state = fields.Selection([('in_progress', 'In Progress'),
                              ('close', 'Closed'),
                              ('posted', 'Posted')], 'State', default='in_progress')
    route_plan_id = fields.Many2one('route.plan', 'Route Plans', required=True)
    order_ids = fields.One2many('van.order', 'daily_sale_summary_id', 'Orders')
    payment_ids = fields.One2many('van.order.payment', 'daily_sale_summary_id', 'Payments')
    picking_ids = fields.One2many('stock.picking', 'daily_sale_summary_id', 'Pickings')
    order_count = fields.Integer(compute='_compute_order_count', string='Order Count')
    picking_count = fields.Integer(compute='_compute_picking_count', string='Picking Count')
    payment_count = fields.Integer(compute='_compute_payment_count', string='Payment Count')

    
    analytic_account_id = fields.Many2one('account.analytic.account', 'Analytic Account')
    company_id = fields.Many2one('res.company', 'Company', required=1, default=lambda self: self.env.company.id)

    def unlink(self):
        raise UserError(_('Cannot delete session(s)'))
        return super(DailySaleSummary, self).unlink()

    @api.onchange('team_id')
    def onchange_team_id(self):
        self.analytic_account_id = self.team_id.analytic_account_id.id

    def _compute_order_count(self):
        for record in self:
            record.order_count = len(record.order_ids)

    def _compute_picking_count(self):
        for record in self:
            record.picking_count = len(record.picking_ids)

    def _compute_payment_count(self):
        for record in self:
            record.payment_count = len(record.payment_ids)

    

    def action_view_orders(self):
        return {
            'name': 'Orders',
            'type': 'ir.actions.act_window',
            'res_model': 'van.order',
            'view_mode': 'tree,form',
            'domain': [('id', 'in', self.order_ids.ids)],
            'context': {'default_daily_sale_summary_id': self.id}
        }

    def action_view_payments(self):
        treeview_ref = self.env.ref('daily_sale_summary.view_van_order_payment_tree', False)

        return {
            'name': 'Payments',
            'type': 'ir.actions.act_window',
            'res_model': 'van.order.payment',
            'view_mode': 'tree,form',
            'view_id': False,
            'domain': [('id', 'in', self.payment_ids.ids)]
        }


    def action_view_pickings(self):
        return {
            'name': 'Delivery',
            'type': 'ir.actions.act_window',
            'res_model': 'stock.picking',
            'view_mode': 'tree,form',
            'domain': [('id', 'in', self.picking_ids.ids)]
        }

    def action_view_move_lines(self):
        invoice_ids = self.order_ids.invoice_ids
        payment_ids = self.env['account.payment'].search([('van_order_id', 'in', self.order_ids.ids)])
        cash_move_ids = payment_ids.move_id
        move_lines = (invoice_ids | cash_move_ids).line_ids.ids
        return {
            'name': _('Journal Items'),
            'type': 'ir.actions.act_window',
            'res_model': 'account.move.line',
            'view_mode': 'tree',
            'view_id': self.env.ref('account.view_move_line_tree_grouped').id,
            'domain': [('id', 'in', move_lines)],
            'context': {
                'journal_type': 'general',
                'search_default_group_by_move': 1,
                'group_by': 'move_id',
                'search_default_posted': 1,
                'name_groupby': 1,
            },
        }

    @api.model
    def create(self, vals):
        team_code = self.env['crm.team'].search([('id','=', vals['team_id'])]).code
        if not team_code:
            raise UserError(_('Please Add a code for Sale Team.'))
        route_plan_code = self.env['route.plan'].search([('id','=', vals['route_plan_id'])]).code
        if not route_plan_code:
            raise UserError(_('Plase Add a code for route plan'))
        vals['name'] = team_code + "-" + route_plan_code + "-" +self.env['ir.sequence'].sudo().next_by_code('daily.sale.summary')
        return super(DailySaleSummary, self).create(vals)

    def action_close(self):
        self.state = 'close'

    def realtime_stock(self):
        self.order_ids.btn_confirm()

    def action_post(self):
        self.order_ids.btn_confirm()
        route_plan_data = self.env['route.plan.checkin'].sudo().search([('route_plan_id','=',self.route_plan_id.id),('check_in','=',True)])
        if route_plan_data:
            route_plan_data.check_in = False
        sale_return_data = self.env['sale.stock.return'].sudo().search([('daily_sale_summary_id','=',self.id)])
        if sale_return_data:
            for return_data in sale_return_data:
                order_lines = []
                for line in return_data.line_ids:
                    order_lines.append(
                        (0, 0, line.prepare_invoice_line())
                    )
                return_data.btn_confirm()
                return_data.btn_validate()
                move_id = self.env['account.move'].sudo().search([('van_order_id','=',return_data.order_ref.id),('move_type','=','out_invoice')])
                for rec in move_id:
                    reverse = rec._reverse_moves_fieldsales()
                    
                    if reverse.state == 'draft':
                        reverse.action_post()
                        receivable_line = reverse.line_ids.filtered_domain([('account_internal_type', '=', 'receivable'), ('reconciled', '=', False)])
                        destination_account_id = receivable_line.account_id

                        for payment in return_data.payment_ids:
                            payment_vals = return_data._prepare_payment(reverse, payment, destination_account_id)
                            
                            if not payment_vals:
                                continue
                            invoice_payment = self.env['account.payment'].sudo().create(payment_vals)
                            invoice_payment.action_post()
                            payment_lines = invoice_payment.line_ids.filtered_domain([('account_internal_type', '=', 'receivable'),('reconciled', '=', False)])
                            for account in payment_lines.account_id:
                                result = (payment_lines + receivable_line).filtered_domain([('account_id', '=', account.id), ('reconciled', '=', False)]).reconcile()
                    
        self.state = 'posted'
