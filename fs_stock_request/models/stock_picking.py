from odoo import api, models, fields
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from odoo.exceptions import UserError
from datetime import datetime


class StockPicking(models.Model):

    _inherit = 'stock.picking'
    _order = 'scheduled_date desc'

    is_requisition = fields.Boolean('Is Requisition?')
    is_fs_return = fields.Boolean('Is Return?')
    is_van_transfer = fields.Boolean('Is Van Transfer?')
    approve_user_id = fields.Many2one('res.users', 'Approved By', domain=[('share', '=', False)])
    team_id = fields.Many2one('crm.team', 'Sales Team', tracking=5, domain=[('is_van_team', '=', True)])
    fleet_id = fields.Many2one('fleet.vehicle', 'Vehicle', tracking=6)
    sender_id = fields.Many2one('res.users', 'Sender', domain=[('share', '=', False)])
    receiver_id = fields.Many2one('res.users', 'Receiver', domain=[('share', '=', False)])
    sender_fleet_id = fields.Many2one('fleet.vehicle', 'Sender Vehicle')
    receiver_fleet_id = fields.Many2one('fleet.vehicle', 'Receiver Vehicle')
    issued_user_id = fields.Many2one('res.users', 'Issued User')
    issued_user_sign = fields.Image('Issued User Sign')
    received_user_id = fields.Many2one('res.users', 'Received User')
    received_user_sign = fields.Image('Received User Sign')
    fs_signature = fields.Image('Signature')

    @api.model
    def get_warehouse(self, location):
        loc_warehouse = self.env['stock.warehouse']
        warehouses = self.env['stock.warehouse'].search([])
        for warehouse in warehouses:
            root_location_id = warehouse.lot_stock_id.id
            location_ids = self.env['stock.location'].search([('id', 'child_of', root_location_id)]).ids
            if location.id in location_ids:
                loc_warehouse = warehouse
                break
        return loc_warehouse

    @api.onchange('location_id', 'is_requisition')
    def onchange_source_location(self):
        if (self.is_requisition or self.is_fs_return) and self.location_id:
            warehouse = self.get_warehouse(self.location_id)
            if not warehouse.int_type_id.id:
                raise UserError('Operation type of Internal Transfer for source location is missing.')
            self.picking_type_id = warehouse.int_type_id.id

    @api.onchange('is_requisition', 'team_id')
    def onchange_team_id(self):
        if self.team_id:
            self.fleet_id = self.team_id.vehicle_id.id
            if self.is_requisition:
                self.location_dest_id = self.team_id.van_location_id.id
            elif self.is_fs_return:
                self.location_id = self.team_id.van_location_id.id

    @api.onchange('picking_type_id', 'partner_id')
    def _onchange_picking_type(self):
        if not self.is_requisition and not self.is_fs_return:
            return super()._onchange_picking_type()

    @api.model
    def create(self, vals):
        date = vals.get('scheduled_date', vals.get('date', False))
        if isinstance(date, str):
            date = datetime.strptime(date, DEFAULT_SERVER_DATETIME_FORMAT)
        if vals.get('is_requisition', False) is True:
            location = self.env['stock.location'].browse(vals['location_id'])
            warehouse = self.get_warehouse(location)
            vals['name'] = f'{warehouse.code}/' + self.env['ir.sequence'].sudo().next_by_code('stock.requisition.sequence', sequence_date=date)
        if vals.get('is_fs_return', False) is True:
            location = self.env['stock.location'].browse(vals['location_id'])
            warehouse = self.get_warehouse(location)
            vals['name'] = f'{warehouse.code}/' + self.env['ir.sequence'].sudo().next_by_code('stock.return.sequence', sequence_date=date)
        return super(StockPicking, self).create(vals)

    def action_confirm(self):
        res = super(StockPicking, self).action_confirm()
        self.approve_user_id = self.env.user.id
        return res
    
    def _action_done(self):
        res = super()._action_done()
        for picking in self.filtered(lambda p: p.state == 'done'):
            picking.write({
                'issued_user_id': self.env.user.id,
                'issued_user_sign': self.env.user.fs_signature,
            })
        return res

    def btn_show_stock_on_hand(self):
        products = self.move_lines.product_id.ids
        if self.is_requisition:
            location_id = self.location_dest_id.id
        else:
            location_id = self.location_id.id
        return {
            'name': 'On Hand',
            'type': 'ir.actions.act_window',
            'res_model': 'stock.quant',
            'view_mode': 'tree',
            'view_id': self.env.ref('fs_stock_request.view_stock_quant_tree_on_hand_only').id,
            'domain': [('product_id', 'in', products),
                       ('location_id', '=', location_id)],
        }
