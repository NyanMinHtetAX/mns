from odoo import models, fields, api,_
from odoo.exceptions import ValidationError, UserError


class DeliveryManPicking(models.Model):
    _name = 'delivery.man.picking'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Delivery Man Picking'
    _rec_name = 'reference_no'
    _order = "id desc"

    picking_id = fields.Many2one('stock.picking', string='Delivery Picking No')
    return_picking_id = fields.Many2one("stock.picking", string="Return Picking No")
    township_id = fields.Many2one('res.township', related='customer_id.township_id', store=True, string='Township')
    assigned_date = fields.Date(string='Assigned Date', tracking=True, default=fields.Date.context_today)
    delivery_date = fields.Date(string='Delivery Date', tracking=True, default=fields.Date.context_today)
    delivery_man_id = fields.Many2one('res.users', string='Delivery Man', tracking=True)
    sale_team_id = fields.Many2one('crm.team', string='Sale Team', tracking=True)
    sale_order_id = fields.Many2one('sale.order', string='Sale Order Ref')
    sale_customer_id = fields.Many2one('res.partner', string='Sale Customer', tracking=True)
    customer_id = fields.Many2one('res.partner', string='Customer', tracking=True)
    delivery_address = fields.Char(string='Delivery Address', tracking=True)
    reference_no = fields.Char(string='Reference No')
    invoice_count = fields.Integer(compute='_compute_orders_number', string='Number of Orders')
    picking_lines = fields.One2many('picking.line', 'delivery_picking_id', string='Delivery Lines')
    back_order_lines = fields.One2many('back.order.line', 'delivery_picking_id', string='Back Order Lines')
    township_code = fields.Char(string='Township Code')
    is_back_order = fields.Boolean(string='BackOrder?', compute='_get_back_order', default=False)
    delivery_note = fields.Text('Delivery Note')
    delivery_remarks = fields.Char('Delivery Remarks')
    invoice_ids = fields.Many2many('account.move', string='Invoices', compute='_compute_invoices')
    state = fields.Selection([('assign', 'Assigned'),
                              ('deliver', 'Delivered'),
                              ('cancel', 'Canceled'),
                              ('pending', 'Pending')], string='State', default='assign', tracking=1)
    partial = fields.Boolean(string='Partial', default=False,compute='_get_partial', store=True)
    
    received_by = fields.Char(string="Received by")
    signature = fields.Image(string='Signature', help='for sign')

        
    @api.depends('picking_lines')
    def _get_partial(self):
        for rec in self.picking_lines:
            if rec.partial:
                self.partial = True

    def _compute_invoices(self):
        for picking in self:
            invoices = picking.sale_order_id.invoice_ids.filtered_domain(
                [('payment_state', 'in', ['not_paid', 'partial'])])
            picking.invoice_ids = [(6, 0, invoices.ids)]

    @api.depends('picking_id', 'sale_order_id')
    def _get_back_order(self):
        for rec in self:
            is_back_order = False
            for line in rec.sale_order_id.order_line:
                diff_qty = line.product_uom_qty - line.qty_delivered
                if diff_qty and self.picking_id.backorder_id:
                    is_back_order = True
            rec.is_back_order = is_back_order

    def unlink(self):
        if 'assign' not in self.mapped('state'):
            raise UserError(_('You cannot delete a Delivery Man Picking Record which is Delivered.'))
        return super(DeliveryManPicking, self).unlink()

    @api.model
    def create(self, vals):
        township_code = vals.get('township_code')
        if not township_code:
            raise ValidationError('Please set township code for this customer in contact setting')
        vals['reference_no'] = 'DMP/' + township_code + '/' + self.env['ir.sequence'].next_by_code('delivery.man.picking') or _('New')

        res = super(DeliveryManPicking, self).create(vals)
        return res

    @api.onchange('sale_order_id')
    def onchange_sale_order(self):
        self.customer_id = self.sale_order_id.partner_id.id

    def deliver(self):
        self.write({'state': 'deliver'})

    def cancel(self):
        self.write({'state': 'cancel'})

    def pending(self):
        self.write({'state': 'pending'})

    def btn_return(self):
        context = self.env.context.copy()
        context.update({
            'default_picking_id': self.picking_id.id,
        })
        return {
            'name': 'Reverse Transfer',
            'type': 'ir.actions.act_window',
            'res_model': 'stock.return.picking',
            'view_mode': 'form',
            'context': context,
            'target': 'new',
        }

    @api.depends('picking_id')
    def _compute_orders_number(self):
        for rec in self:
            rec.invoice_count = len(rec.invoice_ids)
            return_pickings = self.env['stock.picking'].search([
                ('origin', 'ilike', rec.picking_id.name),  # Check if there's a return picking with the same origin
                ('state', '!=', 'cancel'),  # Exclude canceled return pickings
            ], limit=1)
            rec.return_picking_id = return_pickings
        

    def action_open_invoice(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Invoices',
            'res_model': 'account.move',
            'view_mode': 'tree,form',
            'domain': [('id', 'in', self.invoice_ids.ids)],
            'context': {}
        }




class PickingLine(models.Model):
    _name = 'picking.line'
    _description = 'Picking Line'

    delivery_picking_id = fields.Many2one('delivery.man.picking', string='Delivery Man Picking')
    product_id = fields.Many2one('product.product', string='Product')
    description = fields.Text(string='Description')
    date = fields.Datetime(string='Scheduled Date')
    date_deadline = fields.Datetime(string='Deadline')
    product_uom_qty = fields.Float(string='Demand')
    quantity_done = fields.Float(string='Done')
    quantity_return = fields.Text(string="Return Qty")
    partial = fields.Boolean(string="Partial")
    uom_id = fields.Many2one('uom.uom', string='UOM')


class BackOrderLine(models.Model):
    _name = 'back.order.line'
    _description = 'Back Order Lines'

    delivery_picking_id = fields.Many2one('delivery.man.picking', string='Delivery Man Picking')
    product_id = fields.Many2one('product.product', string='Product')
    description = fields.Text(string='Description')
    date = fields.Datetime(string='Scheduled Date')
    date_deadline = fields.Datetime(string='Deadline')
    product_uom_qty = fields.Float(string='Demand')
    quantity_done = fields.Float(string='Done')
    uom_id = fields.Many2one('uom.uom', string='UOM')

