from odoo import models, fields, api, _
from odoo.exceptions import UserError


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    def _get_default_order(self):
        if self.origin:
            sale_order_id = self.env['sale.order'].search([('name', '=', self.origin)]).id
            self.order_id = sale_order_id

    is_assigned = fields.Boolean(string='Have Been Assigned?', default=False)
    delivery_man_picking_count = fields.Integer('Delivery Man Picking Count',
                                                compute='_compute_delivery_man_picking_count')
    delivery_man_picking_ids = fields.One2many('delivery.man.picking', 'picking_id', 'Delivery Man Pickings')
    delivery_remarks = fields.Char('Delivery Remarks')
    delivery_man_id = fields.Many2one('res.users', string='Delivery Man', tracking=True,
                                      domain=[('is_delivery_man', '=', True)])
    sale_team_id = fields.Many2one('crm.team', domain=[('is_van_team','=',True)])
    order_id = fields.Many2one('sale.order', string='Sale Order', default=_get_default_order)
    sale_customer_id = fields.Many2one(related='sale_id.partner_id',string="Sale Customer",tracking=True,store=True)
    vehicle_no = fields.Char(string='Vehicle No')

    def _compute_delivery_man_picking_count(self):
        for picking in self:
            picking.delivery_man_picking_count = len(picking.delivery_man_picking_ids)

    def assign_function(self):
        if any([dp.state in ['deliver', 'cancel'] for dp in self.delivery_man_picking_ids]):
            raise UserError(f'You can\'t assign again. The delivery man picking is already in '
                            f'{self.delivery_man_picking_ids.state} state.')
        picking_id = self.id
        self._get_default_order()
        action = {
            'name': 'Select Delivery Man',
            'type': 'ir.actions.act_window',
            'res_model': 'assign.delivery',
            'context': {
                'default_picking_id': picking_id,
                'default_picking_no': self.name,
                'default_delivery_man_picking_id': self.delivery_man_picking_ids.id,
                'default_order_id': self.order_id.id,
            },
            'target': 'new',
            'view_mode': 'form',
        }
        return action

    def assign_to_delivery_man(self):
        return self.assign_function()

    def re_assign_to_delivery_man(self):
        return self.assign_function()

    def action_show_delivery_man_pickings(self):
        if len(self.delivery_man_picking_ids.ids) > 1:
            action = self.env['ir.actions.act_window']._for_xml_id('base_delivery_man.action_delivery_picking_man')
            action['domain'] = [('id', 'in', self.delivery_man_picking_ids.ids)]
        else:
            action = {
                'name': 'Delivery Pickings',
                'type': 'ir.actions.act_window',
                'res_id': self.delivery_man_picking_ids.id,
                'res_model': 'delivery.man.picking',
                'view_mode': 'form',
            }
        return action

    def assign_delivery_man(self):
        active_ids = self.env.context.get('active_ids', [])
        lines = self.env['stock.picking'].browse(active_ids)
        action = {
            'name': 'Select Sale Team',
            'type': 'ir.actions.act_window',
            'res_model': 'assign.delivery',
            'context': {
                'default_picking_ids': lines.ids,

            },
            'target': 'new',
            'view_mode': 'form',
        }
        return action

    def re_assign_delivery_man(self):
        active_ids = self.env.context.get('active_ids', [])
        lines = self.env['stock.picking'].browse(active_ids)
        action = {
            'name': 'Select Sale Team',
            'type': 'ir.actions.act_window',
            'res_model': 'assign.delivery',
            'context': {
                'default_picking_ids': lines.ids,

            },
            'target': 'new',
            'view_mode': 'form',
        }
        return action
