from odoo import api, models, fields, SUPERUSER_ID
from odoo.exceptions import UserError


class SaleStockReturn(models.Model):

    _name = 'sale.stock.return'
    _description = 'Stock Return from Sale'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char('Name', default='Draft')
    reference = fields.Char('Reference')
    partner_id = fields.Many2one('res.partner', 'Customer', domain=[('customer', '=', True)])
    date = fields.Datetime('Date', default=fields.Datetime.now)
    multi_uom_onhand_qty = fields.Char('Multi UOM On Hand Qty', compute='convert_to_multi_uom')
    team_id = fields.Many2one('crm.team', 'Sales Team')
    sale_man_id = fields.Many2one('res.users', 'Salesman')
    sale_man_ids = fields.Many2many('res.users', string='Available Salesmen', compute='_compute_sale_man_ids')
    route_plan_id = fields.Many2one('route.plan', 'Route Plan')
    type = fields.Selection([('return', 'Sale Return'),
                             ('exchange', 'Stock Exchange')], 'Return Type')
    reason = fields.Selection([('damage', 'Damage'),
                               ('expired', 'Expired'),
                               ('custom', 'Custom')], 'Reason')
    line_ids = fields.One2many('sale.stock.return.line', 'sale_stock_return_id', 'Return Lines')
    remarks = fields.Text('Remarks')
    state = fields.Selection([('draft', 'Draft'),
                              ('confirm', 'Confirm'),
                              ('done', 'Done')], 'State', default='draft')
    
    image_ids = fields.One2many('sale.stock.return.image', 'sale_stock_return_id', 'Images')
    stock_move_ids = fields.One2many('stock.move', 'sale_stock_return_id', 'Stock Moves')
    analytic_account_id = fields.Many2one('account.analytic.account', 'Analytic Account')
    company_id = fields.Many2one('res.company', 'Company', default=lambda self: self.env.company.id)
    order_ref = fields.Many2one('van.order', string="Order Ref")
    daily_sale_summary_id = fields.Many2one('daily.sale.summary', 'Daily Sale Summary', store=True)
    slip_image = fields.Image('Slip Image')
    payment_ids = fields.One2many('sale.return.payment', 'return_id', 'Payments')
    
    description = fields.Text('Description')


    @api.onchange('team_id')
    def onchange_team_id(self):
        self.analytic_account_id = self.team_id.analytic_account_id

    @api.depends('team_id')
    def _compute_sale_man_ids(self):
        for rec in self:
            rec.sale_man_ids = rec.team_id.member_ids

    def btn_confirm(self):
        self.write({
            'state': 'confirm',
        })

    def btn_validate(self):
        if self.stock_move_ids:
            return self._update_pickings()
        location = self.team_id.van_location_id
        customer_location = self.partner_id.property_stock_customer
        in_lines = self.line_ids.filtered(lambda l: l.type == 'in')
        out_lines = self.line_ids - in_lines

        if in_lines:
            picking = self.env['stock.picking'].create(self._prepare_picking_values(customer_location,
                                                                                    location,
                                                                                    location.warehouse_id.in_type_id.id,
                                                                                    in_lines))
            picking.move_lines.move_line_ids.write({'picking_id': picking.id})
            picking.write({
                'daily_sale_summary_id': self.daily_sale_summary_id
            })

        if out_lines:
            picking = self.env['stock.picking'].create(self._prepare_picking_values(location,
                                                                                    customer_location,
                                                                                    location.warehouse_id.out_type_id.id,
                                                                                    out_lines))
            picking.move_lines.move_line_ids.write({'picking_id': picking.id})
            picking.write({
                'daily_sale_summary_id': self.daily_sale_summary_id
            })
        self._update_pickings()

    def _update_pickings(self):
        pickings = self.stock_move_ids.picking_id
        for picking in pickings:
            picking.action_confirm()
            picking._action_done()
        if all([picking.state == 'done' for picking in pickings]):
            self.write({'state': 'done'})

    def btn_show_pickings(self):
        action = self.env['ir.actions.act_window']._for_xml_id('stock.action_picking_tree_all')
        action['domain'] = [('id', 'in', self.stock_move_ids.picking_id.ids)]
        action['context'] = {'create': 0}
        return action

    def btn_show_svl(self):
        action = self.env["ir.actions.actions"]._for_xml_id("stock_account.stock_valuation_layer_action")
        action['domain'] = [('stock_move_id', 'in', self.stock_move_ids.ids)]
        return action

    def _prepare_picking_values(self, loc_src, loc_dest, picking_type_id, lines):
        move_vals = []
        for line in lines:
            move_vals.append((0, 0, line._prepare_stock_move_vals(loc_src, loc_dest)))
        return {
            'partner_id': self.partner_id.id,
            'picking_type_id': picking_type_id,
            'location_id': loc_src.id,
            'location_dest_id': loc_dest.id,
            'scheduled_date': self.date,
            'origin': self.name,
            'analytic_account_id': self.analytic_account_id.id,
            'move_lines': move_vals,
            'company_id': self.company_id.id,
        }


    def _prepare_invoice(self):
        van_order = self.order_ref
        return {
            'ref': van_order.name,
            'move_type': 'out_refund',
            'narration': self.remarks,
            'currency_id': van_order.currency_id.id,
            'user_id': van_order.user_id.id,
            'invoice_user_id': van_order.user_id.id,
            'team_id': van_order.team_id.id,
            'partner_id': van_order.partner_id.id,
            'partner_shipping_id': van_order.partner_id.id,
            'partner_bank_id': self.env.company.partner_id.bank_ids[:1].id,
            'journal_id': van_order.team_id.invoice_journal_id.id,
            'invoice_origin': van_order.name,
            'invoice_line_ids': [],
            'sale_stock_return_id': self.id,
            'analytic_account_id': self.analytic_account_id.id,
            'company_id': self.company_id.id,
            'ks_global_discount_rate': van_order.global_discount_rate,
            'ks_global_discount_type': 'percent' if van_order.global_discount_type == 'percent' else 'amount',
        }

    def _prepare_payment(self, move, payment, destination_account_id):
        available_payment_method_lines = payment.journal_id._get_available_payment_method_lines('inbound')
        if available_payment_method_lines:
            payment_method_line_id = available_payment_method_lines[0]._origin.id
        else:
            payment_method_line_id = False

        return {
            'date': payment.date,
            'amount': payment.amount,
            'payment_type': 'outbound',
            'partner_type': 'customer',
            'ref': move.name,
            'journal_id': payment.journal_id.id,
            'currency_id': payment.currency_id.id,
            'partner_id': self.partner_id.id,
            'payment_method_line_id': payment_method_line_id,
            'destination_account_id': destination_account_id.id,
            'van_order_id': self.id,
            'analytic_account_id': self.analytic_account_id.id,
            'company_id': self.company_id.id,
        }

 
    
    @api.model
    def create(self, vals):
        vals['name'] = self.env['ir.sequence'].with_user(SUPERUSER_ID).next_by_code('sale.stock.return')
        return super().create(vals)

    def unlink(self):
        for rec in self:
            if rec.state == 'done':
                raise UserError('You can\'t delete a sale return which is in done state.')
        return super(SaleStockReturn, self).unlink()


class SaleStockReturnLine(models.Model):

    _name = 'sale.stock.return.line'
    _description = 'Stock Return from Sale Line'

    product_id = fields.Many2one('product.product', 'Product')
    lot_id = fields.Many2one('stock.production.lot', 'Lot/Serial')
    tracking = fields.Selection(related='product_id.tracking')
    qty = fields.Float('Qty', default=1.0)
    multi_uom_line_id = fields.Many2one('multi.uom.line', 'UoM')
    multi_uom_line_ids = fields.Many2many('multi.uom.line', string='UoMs', compute='_compute_multi_uom_line_ids')
    uom_id = fields.Many2one('uom.uom', 'Odoo UoM')
    price_unit = fields.Float('Unit Price', default=1.0)
    price_subtotal = fields.Float('Subtotal', compute='_compute_price_subtotal')
    type = fields.Selection([('in', 'IN'),
                             ('out', 'OUT')], 'Type', default='in')
    expired_date = fields.Date('Expired Date')
    note = fields.Text('Note')
    sale_stock_return_id = fields.Many2one('sale.stock.return', 'Sale Stock Return', ondelete='cascade')

    @api.onchange('product_id')
    def onchange_product_id(self):
        product = self.product_id
        self.multi_uom_line_id = product.multi_uom_line_ids.filtered(lambda l: l.uom_id.id == product.uom_id.id).id

    @api.depends('product_id')
    def _compute_multi_uom_line_ids(self):
        for rec in self:
            rec.multi_uom_line_ids = rec.product_id.multi_uom_line_ids

    @api.depends('qty', 'price_unit')
    def _compute_price_subtotal(self):
        for rec in self:
            rec.price_subtotal = rec.qty * rec.price_unit

    def _check_available_qty(self, location):
        qty = self.multi_uom_line_id.ratio * self.qty
        available_qty = self.env['stock.quant']._get_available_quantity(self.product_id, location, self.lot_id)
        if available_qty < qty:
            err = f'You don\'t have enough stock of {self.product_id.name_get()[0][1]} in {location.complete_name}.'
            raise UserError(err)

    def _prepare_stock_move_vals(self, loc_src, loc_dest):
        parent = self.sale_stock_return_id
        values = {
            'name': self.sale_stock_return_id.name,
            'reference': parent.name,
            'product_id': self.product_id.id,
            'product_uom_qty': self.qty * self.multi_uom_line_id.ratio,
            'product_uom': self.product_id.uom_id.id,
            'multi_uom_line_id': self.multi_uom_line_id.id,
            'date': parent.date,
            'location_id': loc_src.id,
            'location_dest_id': loc_dest.id,
            'partner_id': parent.partner_id.id,
            'company_id': parent.company_id.id,
            'origin': parent.name,
            'analytic_account_id': parent.analytic_account_id.id,
            'sale_stock_return_id': parent.id,
            'sale_stock_return_line_id': self.id,
            'move_line_ids': [(0, 0, {
                'product_id': self.product_id.id,
                'product_uom_qty': 0,
                'product_uom_id': self.product_id.uom_id.id,
                'multi_uom_line_id': self.multi_uom_line_id.id,
                'qty_done': self.qty * self.multi_uom_line_id.ratio,
                'location_id': loc_src.id,
                'location_dest_id': loc_dest.id,
            })],
            'state': 'draft',
        }
        return values

    def prepare_invoice_line(self):
        return {
            'name': self.sale_stock_return_id.order_ref.name,
            'product_id': self.product_id.id,
            'product_uom_id': self.product_id.uom_id.id,
            'multi_uom_line_id': self.multi_uom_line_id.id,
            'quantity': self.qty * self.multi_uom_line_id.ratio,
            'multi_price_unit': self.price_unit,
            'sale_stock_return_line_id': self.id,
            'company_id': self.sale_stock_return_id.order_ref.company_id.id,
        }
