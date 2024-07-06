from odoo import api, models, fields
from odoo.exceptions import UserError


class ConsignmentRequisition(models.Model):

    _name = 'consignment.requisition'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Consignment Requisition'

    def _get_default_warehouse(self):
        return self.env['stock.warehouse'].search([], order='id', limit=1).id

    name = fields.Char('Name', default='Draft')
    date = fields.Datetime('Date', default=fields.Datetime.now, required=True)
    partner_id = fields.Many2one('res.partner', 'Customer', domain=[('consignee', '=', True)], required=True)
    pricelist_id = fields.Many2one('product.pricelist', 'Pricelist', required=True)
    currency_id = fields.Many2one('res.currency', 'Currency', related='pricelist_id.currency_id', store=True)
    team_id = fields.Many2one('crm.team', 'Sales Team', domain=[('is_van_team', '=', True)], required=True)
    user_ids = fields.Many2many('res.users', 'Salesmen', compute='_compute_user_ids')
    user_id = fields.Many2one('res.users', 'Salesman', domain="[('id', 'in', user_ids)]", required=True)
    warehouse_id = fields.Many2one('stock.warehouse', 'Warehouse', required=True, default=_get_default_warehouse)
    analytic_account_id = fields.Many2one('account.analytic.account', 'Analytic Account')
    type = fields.Selection([('consignment', 'Consignment'),
                             ('sample', 'Sample')], 'Type', default='consignment', required=True)
    requisition_line_ids = fields.One2many('consignment.line', 'requisition_id', 'Requisition Lines')
    origin = fields.Char('Source Document')
    company_id = fields.Many2one('res.company', 'Company', default=lambda self: self.env.company.id) 
    remarks = fields.Text('Remarks')   
    move_ids = fields.One2many('stock.move', 'consignment_requisition_id', 'Stock Moves') 
    state = fields.Selection([('draft', 'Draft'),
                              ('approve', 'Approved'),
                              ('validate', 'Validated'),
                              ('deliver', 'Delivered')], default='draft', required=True) 

    @api.onchange('partner_id')
    def onchange_partner_id(self):
        self.pricelist_id = self.partner_id.property_product_pricelist                   
    
    @api.depends('team_id')
    def _compute_user_ids(self):
        for record in self:
            record.user_ids = record.team_id.member_ids
    
    @api.model
    def create(self, vals):
        vals['name'] = self.env['ir.sequence'].next_by_code('consignment.requisition')
        return super().create(vals)
    
    def _transfer_to_sale_team(self):
        self.ensure_one()
        loc_src = self.warehouse_id.lot_stock_id
        loc_dest = self.team_id.van_location_id
        picking_type_id = self.warehouse_id.int_type_id
        picking = self.env['stock.picking'].create(self._prepare_picking_values(parter_id=False,
                                                                                loc_src=loc_src,
                                                                                loc_dest=loc_dest,
                                                                                picking_type_id=picking_type_id))
        move_vals = []
        for line in self.requisition_line_ids:
            line._check_available_qty(loc_src)
            move_vals.append(line._prepare_stock_move_vals(picking, loc_src, loc_dest))
        moves = self.env['stock.move'].create(move_vals)


    def action_approve(self):
        for record in self:
            record.write({'state': 'approve'})

    def action_validate(self):
        for record in self:
            record.transfer_to_sale_team()
            record.write({'state': 'validate'})

    def action_deliver(self):
        for record in self:
            record.write({'state': 'deliver'})
    
    def _prepare_picking_values(self, partner_id, loc_src, loc_dest, picking_type_id):
        return {
            'partner_id': partner_id,
            'picking_type_id': picking_type_id,
            'location_id': loc_src.id,
            'location_dest_id': loc_dest.id,
            'scheduled_date': self.date,
            'origin': self.name,
            'analytic_account_id': self.analytic_account_id.id,
            'company_id': self.company_id.id,
        }
    

class ConsignmentLine(models.Model):

    _name = 'consignment.requisition.line'
    _description = 'Consignment Line'

    product_id = fields.Many2one('product.product', 'Product', required=True)
    qty = fields.Float('Qty', required=True, default=1)
    lot_id = fields.Many2one('stock.production.lot', 'Lot/Serial', domain="[('product_id', '=', product_id)]")
    tracking = fields.Selection(string='Tracking', related='product_id.tracking')
    multi_uom_line_id = fields.Many2one('multi.uom.line', 'Multi UoM Line', required=True)
    multi_uom_line_ids = fields.Many2many('multi.uom.line', 'Multi UoM Line', compute='_compute_multi_uom_line_ids')
    uom_id = fields.Many2one('uom.uom', related='multi_uom_line_id.uom_id', store=True)
    price_unit = fields.Monetary('Price Unit', required=True, default=1, currency_field='currency_id')
    price_subtotal = fields.Monetary('Price Subtotal', compute='_compute_price_subtotal', store=True, currency_field='currency_id')
    currency_id = fields.Many2one('res.currency', 'Currency', compute='_compute_currency')
    requisition_id = fields.Many2one('consignment.requisition', 'Requisition', ondelete='cascade')
    requisition_state = fields.Selection(string='Requisition State', related='requisition_id.state')

    @api.onchange('product_id')
    def onchange_product_id(self):
        if self.product_id:
            product = self.product_id
            self.multi_uom_line_id = product.multi_uom_line_ids.filtered(lambda l: l.uom_id.id == product.uom_id.id).id

    @api.onchange('product_id', 'multi_uom_line_id', 'qty')
    def calculate_price_unit(self):
        if self.multi_uom_line_id:
            qty = self.multi_uom_line_id.ratio * self.qty
            product = self.product_id.with_context(
                lang=self.requisition_id.partner_id.lang,
                partner=self.requisition_id.partner_id,
                quantity=qty,
                date=self.requisition_id.date,
                pricelist=self.requisition_id.pricelist_id.id,
                uom=self.uom_id.id,
            )
            self.price_unit = product.price * self.multi_uom_line_id.ratio

    @api.depends('product_id')
    def _compute_multi_uom_line_ids(self):
        for line in self:
            line.multi_uom_line_ids = line.product_id.multi_uom_line_ids

    @api.depends('qty', 'price_unit')
    def _compute_price_subtotal(self):
        for line in self:
            line.price_subtotal = line.qty * line.price_unit
    
    @api.depends('requisition_id')
    def _compute_currency(self):
        for line in self:
            line.currency_id = line.requisition_id.currency_id

    def _check_available_qty(self, location):
        qty = self.multi_uom_line_id.ratio * self.qty
        available_qty = self.env['stock.quant']._get_available_quantity(self.product_id, location, self.lot_id)
        if available_qty < qty:
            err = f'You don\'t have enough stock of {self.product_id.name_get()[0][1]} in {location.complete_name}.'
            raise UserError(err)

    def _prepare_stock_move_vals(self, picking, loc_src, loc_dest):
        parent = self.requisition_id
        return {
            'name': self.product_id.name_get()[0][1],
            'reference': picking.name,
            'product_id': self.product_id.id,
            'product_uom_qty': self.qty * self.multi_uom_line_id.ratio,
            'product_uom': self.prodct_id.uom_id.id,
            'multi_uom_line_id': self.multi_uom_line_id.id,
            'date': parent.date,
            'location_id': loc_src.id,
            'location_dest_id': loc_dest.id,
            'partner_id': picking.partner_id.id,
            'company_id': picking.company_id.id,
            'origin': parent.name,
            'analytic_account_id': parent.analytic_account_id.id,
            'picking_id': picking.id,
            'consignment_line_id': self.id,
            'consignment_requisition_id': parent.id,
            'move_line_ids': [(0, 0, {
                'product_id': self.product_id.id,
                'product_uom_qty': 0,
                'product_uom_id': self.product_id.uom_id.id,
                'multi_uom_line_id': self.multi_uom_line_id.id,
                'qty_done': self.qty * self.multi_uom_line_id.ratio,
                'location_id': loc_src.id,
                'location_dest_id': loc_dest.id,
                'picking_id': picking.id,
            })],
            'state': 'draft',
        }
