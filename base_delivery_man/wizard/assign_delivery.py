from odoo import api, models, fields, _
from odoo.exceptions import UserError
from markupsafe import Markup


class AssignDelivery(models.TransientModel):
    _name = 'assign.delivery'
    _description = 'Assign To Delivery Man'
    _rec_name = 'sale_team_id'

    delivery_man_id = fields.Many2one('res.users', string='Delivery Man', domain=[('is_delivery_man', '=', True),
                                                                                  ('is_portal_user', '=', True)])
    sale_team_id = fields.Many2one('crm.team', string='Sale Team', domain=[('is_van_team', '=', True)])
    picking_no = fields.Char(string='Picking Number')
    picking_id = fields.Many2one('stock.picking', string='Picking ID')
    delivery_man_picking_id = fields.Many2one('delivery.man.picking')
    order_id = fields.Many2one('sale.order', string='Sale Order')
    picking_ids = fields.Many2many('stock.picking', string='PICKINGS')

    def assign_delivery(self):
        picking_no = ''
        data_list = []
        if self.picking_ids:

            for picking in self.picking_ids:
                data_list.append(picking.name)
                picking_no = picking.name
                sale_order_id = self.env['sale.order'].search([('name', '=', picking.origin)]).id
                self.order_id = sale_order_id
                picking.is_assigned = True
                picking.delivery_man_id = self.delivery_man_id.id
                picking.sale_team_id = self.sale_team_id.id
                township_code = picking.partner_id.township_id.code
                delivery_pickings = self.env['delivery.man.picking'].search([('picking_id', '=', picking.id)])
                if not delivery_pickings:
                    delivery_man = self.env['delivery.man.picking'].create({
                        'picking_id': picking.id,
                        'sale_order_id': self.order_id.id,
                        'sale_customer_id': self.order_id.partner_id.id,
                        'customer_id': picking.partner_id.name,
                        'assigned_date': fields.Date.today(),
                        'delivery_date': fields.Date.today(),
                        'sale_team_id': self.sale_team_id.id,
                        'township_code': township_code,
                        'delivery_note': 'picking.note and Markup(picking.note).striptags()',
                        'picking_lines': [
                            (0, 0,
                             {
                                 'product_id': rec.product_id.id,
                                 'description': rec.description_picking,
                                 'date': rec.date,
                                 'date_deadline': rec.date_deadline,
                                 'product_uom_qty': rec.product_uom_qty,
                                 'quantity_done': rec.multi_quantity_done,
                                 'uom_id': rec.multi_uom_line_id.uom_id.id,
                             }
                             )
                            for rec in picking.move_lines
                        ],
                    })
                    for rec in self.order_id.order_line:
                        diff_qty = rec.product_uom_qty - rec.qty_delivered
                        if diff_qty > 0 and self.picking_id.backorder_id:
                            delivery_man.write({
                                'back_order_lines': [
                                    (0, 0, {
                                        'product_id': rec.product_id.id,
                                        'product_uom_qty': rec.multi_quantity_done - rec.multi_qty_delivered,
                                        'uom_id': rec.multi_uom_line_id.uom_id.id,
                                    })
                                ],
                            })
                else:

                    delivery_pickings.write({'sale_team_id': self.sale_team_id.id})

        else:
            picking_no = self.picking_no
            self.picking_id.delivery_man_id = self.delivery_man_id.id
            self.picking_id.sale_team_id = self.sale_team_id.id
            self.picking_id.is_assigned = True
            township_code = self.order_id.partner_id.township_id.code
            delivery_pickings = self.env['delivery.man.picking'].search([('picking_id', '=', self.picking_id.id)])
            if not delivery_pickings:
                delivery_man = self.env['delivery.man.picking'].create({
                    'picking_id': self.picking_id.id,
                    'return_picking_id': None,
                    'sale_order_id': self.order_id.id,
                    'sale_customer_id': self.order_id.partner_id.id,
                    'customer_id': self.picking_id.partner_id.id,
                    'delivery_address': self.picking_id.partner_id.name,
                    'assigned_date': fields.Date.today(),
                    'delivery_date': fields.Date.today(),
                    'sale_team_id': self.sale_team_id.id,
                    'township_code': self.picking_id.partner_id.township_id.code,
                    'delivery_note': self.picking_id.note and Markup(self.picking_id.note).striptags(),
                    'picking_lines': [
                        (0, 0,
                         {
                             'product_id': rec.product_id.id,
                             'description': rec.description_picking,
                             'date': rec.date,
                             'date_deadline': rec.date_deadline,
                             'product_uom_qty': rec.product_uom_qty,
                             'quantity_return': 0,
                             'quantity_done': rec.multi_quantity_done,
                             'uom_id': rec.multi_uom_line_id.uom_id.id,
                         }
                         )
                        for rec in self.picking_id.move_lines
                    ],
                })
                for rec in self.order_id.order_line:
                    diff_qty = rec.product_uom_qty - rec.qty_delivered
                    back_id = self.picking_id.id + 1
                    backorder_data = self.env['stock.picking'].sudo().search([('id', '=', back_id)])
                    if diff_qty > 0 and backorder_data:
                        delivery_man.write({
                            'back_order_lines': [
                                (0, 0, {
                                    'product_id': rec.product_id.id,
                                    'product_uom_qty': rec.multi_uom_qty - rec.multi_qty_delivered,
                                    'uom_id': rec.multi_uom_line_id.uom_id.id,
                                })
                            ],
                        })
            else:
                self.delivery_man_picking_id.write({'sale_team_id': self.sale_team_id.id})

        action = {
            'name': 'Message',
            'type': 'ir.actions.act_window',
            'res_model': 'alert.delivery',
            'context': {
                'default_alert_name': 'Sale Team picking with reference ID ' + picking_no if not data_list else " , ".join(data_list) + ' has been assigned.',
            },
            'target': 'new',
            'view_mode': 'form',
        }
        return action


class AlertDelivery(models.TransientModel):
    _name = 'alert.delivery'
    _description = 'Alert When Deliver man has been assigned'

    alert_name = fields.Char(string='Alert')
