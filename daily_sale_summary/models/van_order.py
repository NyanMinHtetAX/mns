from odoo import api, models, fields, SUPERUSER_ID
from odoo.exceptions import UserError
from odoo.addons.fs_sale_promotion.models.promotion_program import Reward, OrderLine, LineDiscount


class VanOrder(models.Model):

    _name = 'van.order'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Van Order'

    name = fields.Char('Name', default='Draft')
    date = fields.Datetime('Date', required=True, default=fields.Datetime.now)
    partner_id = fields.Many2one('res.partner', 'Partner', required=True)
    warehouse_id = fields.Many2one('stock.warehouse', 'Warehouse', required=True)
    location_id = fields.Many2one('stock.location', 'Location')
    fleet_id = fields.Many2one('fleet.vehicle', 'Fleet', required=True)
    team_id = fields.Many2one('crm.team', 'Sales Team', required=True, domain=[('is_van_team', '=', True)])
    user_id = fields.Many2one('res.users', 'Sales Person', default=lambda self: self.env.user.id)
    order_line_ids = fields.One2many('van.order.line', 'order_id', 'Order Lines')
    picking_ids = fields.One2many('stock.picking', 'van_order_id', 'Picking')
    picking_count = fields.Integer('Picking Count', compute='_compute_picking_count')
    pricelist_id = fields.Many2one('product.pricelist', 'Pricelist', required=True)
    available_pricelist_ids = fields.Many2many('product.pricelist', string='Available Pricelists', compute='_compute_available_pricelists')
    currency_id = fields.Many2one('res.currency', 'Currency', related='pricelist_id.currency_id', store=True)
    amount_untaxed = fields.Monetary('Untaxed', currency_field='currency_id', compute='_compute_amount_all', store=True)
    amount_tax = fields.Monetary('Tax', currency_field='currency_id', compute='_compute_amount_all', store=True)
    amount_total = fields.Monetary('Total', currency_field='currency_id', compute='_compute_amount_all', store=True)
    payment_ids = fields.One2many('van.order.payment', 'order_id', 'Payments')
    remarks = fields.Text('Internal Note')
    invoice_ids = fields.One2many('account.move', 'van_order_id', 'Invoices')
    invoice_count = fields.Integer('Invoice Count', compute='_compute_invoice_count')
    daily_sale_summary_id = fields.Many2one('daily.sale.summary', 'Daily Sale Summary')
    company_id = fields.Many2one('res.company', default=lambda self: self.env.company.id)
    slip_image = fields.Image('Slip Image')
    signature = fields.Image('Signature')

    payment_type = fields.Selection([('cash', 'Cash'),
                                     ('partial', 'Partial'),
                                     ('credit', 'Credit')], 'Payment Type', default='cash')
    state = fields.Selection([('draft', 'New'),
                              ('invoice', 'Invoiced'),
                              ('done', 'Posted'),
                              ('cancel', 'Cancelled')], default='draft')
    global_discount_amt = fields.Monetary('Global Discount', currency_field='currency_id', compute='_compute_amount_all', store=True)
    global_discount_rate = fields.Float('Global Discount Rate')
    global_discount_type = fields.Selection([('fixed', 'Fixed'),
                                             ('percent', 'Percentage')], 'Global Discount Type', default='fixed')
    analytic_account_id = fields.Many2one('account.analytic.account', 'Analytic Account')
    available_promotions = fields.Many2many('promotion.program', string='Available Promotions', compute='_compute_available_promotions')

    order_reference = fields.Char(string='Order Reference')
    latitude = fields.Float("Lat", digits=(24, 12))
    longitude = fields.Float("Long", digits=(24, 12))
    promotion_ids = fields.Many2many('promotion.program', 'promotion_program_val_order_rel', 'van_order_id',
                                     'promotion_program_id', string='Promotions', )
    property_payment_term_id = fields.Many2one('account.payment.term', string='Payment Terms')

    def unlink(self):
        for i in self:
            if i.state in ['draft','done']:
                raise UserError('Cannot delete order(s)')
        return super(VanOrder, self).unlink()

    def btn_show_map(self):
        ctx = self.env.context.copy()

        ctx.update({
            'default_latitude': self.partner_id.latitude,
            'default_longitude': self.partner_id.longitude,
            'default_latitude1': self.latitude,
            'default_longitude1': self.longitude,
            'customer_name': self.partner_id.name,
            'order_name': self.name,
        })

        return {
            'name': 'Van Order Map',
            'type': 'ir.actions.act_window',
            'res_model': 'visit.report.map',
            'view_mode': 'form',
            'context': ctx,
        }

    @api.onchange('daily_sale_summary_id')
    def onchange_daily_sale_summary_id(self):
        self.analytic_account_id = self.daily_sale_summary_id.analytic_account_id.id

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

    @api.onchange('partner_id')
    def onchange_partner(self):
        if self.partner_id.property_product_pricelist:
            self.pricelist_id = self.partner_id.property_product_pricelist
        elif self.partner_id:
            self.pricelist_id = self.env['product.pricelist'].search([], order='id asc', limit=1).id

    @api.onchange('team_id')
    def onchange_team_id(self):
        sales_team = self.team_id
        self.fleet_id = sales_team.vehicle_id.id
        self.location_id = sales_team.van_location_id.id

    @api.onchange('location_id')
    def onchange_location(self):
        if self.location_id:
            self.warehouse_id = self.get_warehouse(self.location_id).id

    def _compute_available_promotions(self):
        for order in self:
            if order.date:
                programs = self.env['promotion.program']._get_available_programs(order.date.date(), order.team_id)
                order.available_promotions = [(6, 0, programs.ids)]
            else:
                order.available_promotions = []

    def _compute_picking_count(self):
        for order in self:
            order.picking_count = len(order.picking_ids)

    def _compute_invoice_count(self):
        for order in self:
            order.invoice_count = len(order.invoice_ids.filtered(
                lambda invoice: invoice.move_type in ['out_invoice', 'out_refund', 'out_receipt']
            ))

    @api.depends('partner_id')
    def _compute_available_pricelists(self):
        for order in self:
            partners = self.env['res.partner'].search([('customer', '=', True),('company_id','=',self.env.company.id)])
            order.available_pricelist_ids = partners.property_product_pricelist.ids

    @api.depends('global_discount_type',
                 'global_discount_rate',
                 'order_line_ids.product_id',
                 'order_line_ids.qty',
                 'order_line_ids.price_unit',
                 'order_line_ids.discount_type',
                 'order_line_ids.discount',
                 'order_line_ids.tax_ids')
    def _compute_amount_all(self):
        for order in self:
            amount_untaxed = sum(order.order_line_ids.mapped('price_untaxed'))
            amount_total = sum(order.order_line_ids.mapped('price_subtotal'))
            amount_tax = amount_total - amount_untaxed
            if order.global_discount_type == 'fixed':
                discount_amt = order.global_discount_amt = order.global_discount_rate
                amount_total -= discount_amt
            else:
                discount_amt = order.global_discount_amt = amount_total * (order.global_discount_rate / 100)
                amount_total -= discount_amt
            order.update({
                'amount_untaxed': amount_untaxed,
                'amount_tax': amount_tax,
                'amount_total': amount_total,
            })

    def btn_show_pickings(self):
        picking_ids = self.picking_ids
        if len(picking_ids) > 1:
            action = {
                'name': 'Delivery',
                'type': 'ir.actions.act_window',
                'res_model': 'stock.picking',
                'view_mode': 'tree,form',
                'domain': [('id', 'in', picking_ids.ids)],
            }
        elif len(picking_ids) == 1:
            action = {
                'name': 'Delivery',
                'type': 'ir.actions.act_window',
                'res_model': 'stock.picking',
                'view_mode': 'form',
                'res_id': picking_ids.id,
            }
        else:
            action = {}
        return action

    def btn_show_invoices(self):
        invoice_ids = self.invoice_ids.filtered(
            lambda invoice: invoice.move_type in ['out_invoice', 'out_refund', 'out_receipt']
        )
        if len(invoice_ids) > 1:
            action = {
                'name': 'Invoices',
                'type': 'ir.actions.act_window',
                'res_model': 'account.move',
                'view_mode': 'tree,form',
                'domain': [('id', 'in', invoice_ids.ids)],
            }
        elif len(invoice_ids) == 1:
            action = {
                'name': 'Delivery',
                'type': 'ir.actions.act_window',
                'res_model': 'account.move',
                'view_mode': 'form',
                'res_id': invoice_ids.id,
            }
        else:
            action = {}
        return action

    def _prepare_picking_values(self):
        partner_loc = self.partner_id.property_stock_customer
        customer_loc, supplier_loc = self.warehouse_id._get_partner_locations()
        return {
            'location_id': self.warehouse_id.lot_stock_id.id,
            'location_dest_id': partner_loc and partner_loc.id or customer_loc.id,
            'picking_type_id': self.warehouse_id.out_type_id.id,
            'partner_id': self.partner_id.id,
            'scheduled_date': self.date,
            'payment_term_id': self.property_payment_term_id.id,
            'origin': self.name,
            'company_id': self.company_id.id,
            'van_order_id': self.id,
            'analytic_account_id': self.analytic_account_id.id,
        }

    def _process_delivery(self):
        moves = []
        order_line_ids = self.order_line_ids.filtered(lambda l: l.product_id.detailed_type == 'product')
        if not order_line_ids:
            return
        picking = self.env['stock.picking'].create(self._prepare_picking_values())
        for order_line in order_line_ids:
            product = order_line.product_id
            location = picking.location_id
            available_qty = self.env['stock.quant']._get_available_quantity(product, location)
            order_line_qty = order_line.qty * order_line.multi_uom_line_id.ratio
            if available_qty < order_line_qty:
                raise UserError(f'Not enough stock of {product.name} in {location.complete_name}.')
            moves.append(order_line._prepare_stock_move_values(picking))
        self.env['stock.move'].create(moves)
        picking._action_done()

    def _prepare_invoice(self):
        return {
            'ref': self.name,
            'move_type': 'out_invoice',
            'narration': self.remarks,
            'currency_id': self.currency_id.id,
            'user_id': self.user_id.id,
            'invoice_user_id': self.user_id.id,
            'team_id': self.team_id.id,
            'partner_id': self.partner_id.id,
            'partner_shipping_id': self.partner_id.id,
            'partner_bank_id': self.env.company.partner_id.bank_ids[:1].id,
            'journal_id': self.team_id.invoice_journal_id.id,
            'invoice_origin': self.name,
            'invoice_line_ids': [],
            'van_order_id': self.id,
            'analytic_account_id': self.analytic_account_id.id,
            'company_id': self.company_id.id,
            'ks_global_discount_rate': self.global_discount_rate,
            'ks_global_discount_type': 'percent' if self.global_discount_type == 'percent' else 'amount',
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
            'payment_type': 'inbound',
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

    def _process_invoice(self):
        move_values = self._prepare_invoice()
        order_lines = []
        for line in self.order_line_ids:
            order_lines.append(
                (0, 0, line.prepare_invoice_line())
            )
        move_values['invoice_line_ids'] = order_lines
        move = self.env['account.move'].with_user(SUPERUSER_ID).create(move_values)
        move._post()
        receivable_line = move.line_ids.filtered_domain([('account_internal_type', '=', 'receivable'),
                                                         ('reconciled', '=', False)])
        destination_account_id = receivable_line.account_id
        for payment in self.payment_ids:
            payment_vals = self._prepare_payment(move, payment, destination_account_id)
            if not payment_vals:
                continue
            invoice_payment = self.env['account.payment'].with_user(SUPERUSER_ID).create(payment_vals)
            invoice_payment.action_post()
            payment_lines = invoice_payment.line_ids.filtered_domain([('account_internal_type', '=', 'receivable'),
                                                                      ('reconciled', '=', False)])
            for account in payment_lines.account_id:
                (payment_lines + receivable_line).filtered_domain([('account_id', '=', account.id), ('reconciled', '=', False)]).reconcile()
        if move.amount_residual == 0:
            self.state = 'done'
        else:
            self.state = 'invoice'

    def btn_confirm(self):
        for order in self:
            order.write({
                'name': self.env['ir.sequence'].with_user(SUPERUSER_ID).next_by_code('van.order.sequence'),
            })
            order._process_delivery()
            order._process_invoice()

    def btn_cancel(self):
        for order in self:
            order.write({'state': 'cancel'})

    def btn_apply_promotion_program(self):
        rewards = {}
        self.remove_promotions()
        lines = [OrderLine(line.id,
                           line.product_id.id,
                           line.qty,
                           line.multi_uom_line_id,
                           self.currency_id._convert(line.price_unit,
                                                     self.company_id.currency_id,
                                                     self.company_id,
                                                     self.date.date()),
                           self.currency_id._convert(line.price_subtotal,
                                                     self.company_id.currency_id,
                                                     self.company_id,
                                                     self.date.date())
                           ) for line in self.order_line_ids]
        order_amount = self.currency_id._convert(self.amount_total,
                                                 self.company_id.currency_id,
                                                 self.company_id,
                                                 self.date.date())
        self._compute_available_promotions()
        for promotion in self.available_promotions:
            method = getattr(promotion, f'_apply_{promotion.type}')
            promotion_rewards = method(lines, order_amount)
            if promotion_rewards:
                rewards[promotion.id] = promotion_rewards
        lines_to_create = []
        for key, promotion_rewards in rewards.items():
            for reward in promotion_rewards:
                if type(reward) == Reward:
                    promotion = self.env['promotion.program'].browse(reward.promotion_id)
                    product = self.env['product.product'].browse(reward.product_id)
                    multi_uom_line_id = product.multi_uom_line_ids.filtered(lambda l: l.uom_id.id == product.uom_id.id)
                    price = self.company_id.currency_id._convert(reward.price,
                                                                 self.currency_id,
                                                                 self.company_id,
                                                                 self.date.date())
                    if reward.promotion_type =='foc':
                        
                        values = {
                            'name': promotion.name,
                            'product_id': reward.product_id,
                            'uom_id': product.uom_id.id,
                            'multi_uom_line_id': multi_uom_line_id.id,
                            'qty': reward.qty,
                            'price_unit': price,
                            'is_foc': True,
                            'tax_ids': False,
                            'order_id': self.id,
                            'promotion_id': reward.promotion_id,
                            'promotion_account_id': reward.account_id,
                        }
                    else:
                        values = {
                            'name': promotion.name,
                            'product_id': reward.product_id,
                            'uom_id': product.uom_id.id,
                            'multi_uom_line_id': multi_uom_line_id.id,
                            'qty': reward.qty,
                            'price_unit': price,
                            'is_foc': False,
                            'tax_ids': False,
                            'order_id': self.id,
                            'promotion_id': reward.promotion_id,
                            'promotion_account_id': reward.account_id,
                        }
                    lines_to_create.append(values)
                elif type(reward) == LineDiscount:
                    self.env['van.order.line'].browse(reward.line_id).update({
                        'discount_type': 'fixed' if reward.type == 'fixed' else 'percent',
                        'is_foc': False,
                        'discount': reward.discount,
                    })
        self.env['van.order.line'].create(lines_to_create)

    def remove_promotions(self):
        promotion_lines = self.order_line_ids.filtered(lambda l: l.promotion_id)
        promotion_lines.unlink()


class VanOrderLine(models.Model):

    _name = 'van.order.line'
    _description = 'Van Order Line'

    name = fields.Char('Description')
    product_id = fields.Many2one('product.product', 'Product', required=1)
    qty = fields.Float('Qty', default=1.0)
    product_uom_qty = fields.Float('Product UOM Qty',compute='_compute_uom_qty',store=True)
    uom_id = fields.Many2one('uom.uom', 'UOM', related='multi_uom_line_id.uom_id', store=True)
    multi_uom_line_id = fields.Many2one('multi.uom.line', 'UoM', required=1)
    multi_uom_line_ids = fields.One2many('multi.uom.line', string='Available UoM', related='product_id.multi_uom_line_ids')
    price_unit = fields.Monetary('Unit Price', currency_field='currency_id', default=1.0)
    price_untaxed = fields.Monetary('Untaxed',
                                    currency_field='currency_id',
                                    compute='_compute_price_subtotal',
                                    store=True)
    price_subtotal = fields.Monetary('Subtotal',
                                     currency_field='currency_id',
                                     compute='_compute_price_subtotal',
                                     store=True)
    refund_line_id = fields.Many2one('van.order.line', 'Refund Line')
    discount_type = fields.Selection([('percent', 'Percent'),
                                      ('fixed', 'Fixed')], default='percent')
    discount = fields.Float('Discount')
    currency_id = fields.Many2one('res.currency', related='order_id.currency_id', store=True)
    tax_ids = fields.Many2many('account.tax', 'van_order_line_tax_rel', 'line_id', 'tax_id', 'Taxes',
                               domain=[('type_tax_use', '=', 'sale')])
    order_id = fields.Many2one('van.order', 'Order', ondelete='cascade')
    promotion_id = fields.Many2one('promotion.program', 'Promotion')
    promotion_account_id = fields.Many2one('account.account', 'Promotion COA')
    is_foc = fields.Boolean('FOC', default=False)

    @api.depends('multi_uom_line_id', 'qty')
    def _compute_uom_qty(self):

        for i in self:
            i.product_uom_qty = i.multi_uom_line_id.ratio * i.qty

    @api.depends('multi_uom_line_id', 'qty')
    def _run_uom_qty(self):
        vol_data = self.env['van.order.line'].sudo().search([])
        for i in vol_data:
            i.product_uom_qty = i.multi_uom_line_id.ratio * i.qty

    @api.onchange('product_id')
    def onchange_product(self):
        multi_uom_line_id = self.product_id.multi_uom_line_ids.filtered(
            lambda line: line.uom_id.id == self.product_id.uom_id.id
        )
        self.multi_uom_line_id = multi_uom_line_id.id
        self.name = self.product_id.name

    @api.onchange('product_id', 'multi_uom_line_id', 'qty')
    def calculate_price_unit(self):
        if self.multi_uom_line_id:
            pricelist_mode = self.env['ir.config_parameter'].get_param('product.product_pricelist_setting')

            if pricelist_mode == 'uom':
                price_unit = self.order_id.pricelist_id._get_pricelist_uom_price(self.product_id,self.multi_uom_line_id,self.qty)
                self.price_unit = price_unit
            else:
                qty = self.multi_uom_line_id.ratio * self.qty
                product = self.product_id.with_context(
                    lang=self.order_id.partner_id.lang,
                    partner=self.order_id.partner_id,
                    quantity=qty,
                    date=self.order_id.date,
                    pricelist=self.order_id.pricelist_id.id,
                    uom=self.uom_id.id,
                )
                self.price_unit = product.price * self.multi_uom_line_id.ratio

    @api.depends('product_id', 'qty', 'price_unit', 'discount_type', 'discount', 'tax_ids')
    def _compute_price_subtotal(self):
        for line in self:
            qty = line.qty
            price_unit = line.price_unit
            discount_type = line.discount_type
            discount = line.discount
            if discount_type == 'fixed':
                price_wo_discount = price_unit - discount
            else:
                price_wo_discount = price_unit * (1 - discount / 100)
            if line.tax_ids:
                tax_data = line.tax_ids.compute_all(
                    price_wo_discount,
                    quantity=qty,
                )
                line.price_subtotal = tax_data['total_included']
                line.price_untaxed = tax_data['total_excluded']
            else:
                line.price_subtotal = line.price_untaxed = price_wo_discount * qty

    def _prepare_stock_move_values(self, picking):
        values = {
            'name': self.product_id.name_get()[0][1],
            'reference': picking.name,
            'product_id': self.product_id.id,
            'product_uom_qty': self.qty * self.multi_uom_line_id.ratio,
            'product_uom': self.product_id.uom_id.id,
            'multi_uom_line_id': self.multi_uom_line_id.id,
            'date': picking.scheduled_date,
            'location_id': picking.location_id.id,
            'location_dest_id': picking.location_dest_id.id,
            'picking_id': picking.id,
            'partner_id': picking.partner_id.id,
            'state': 'draft',
            'company_id': picking.company_id.id,
            'picking_type_id': picking.picking_type_id.id,
            'origin': picking.origin,
            'description_picking': self.product_id.name,
            'van_order_line_id': self.id,
            'move_line_ids': [(0, 0, {
                'product_id': self.product_id.id,
                'product_uom_qty': 0,
                'product_uom_id': self.product_id.uom_id.id,
                'multi_uom_line_id': self.multi_uom_line_id.id,
                'qty_done': self.qty * self.multi_uom_line_id.ratio,
                'location_id': picking.location_id.id,
                'location_dest_id': picking.location_dest_id.id,
                'picking_id': picking.id,
            })],
        }
        return values

    def prepare_invoice_line(self):
        return {
            'name': self.name,
            'product_id': self.product_id.id,
            'product_uom_id': self.product_id.uom_id.id,
            'multi_uom_line_id': self.multi_uom_line_id.id,
            'quantity': self.qty * self.multi_uom_line_id.ratio,
            'discount': self.discount / self.multi_uom_line_id.ratio if self.discount_type == 'fixed' else self.discount,
            'multi_uom_discount': self.discount,
            'discount_type': self.discount_type if self.discount_type == 'fixed' else 'percentage',
            'multi_price_unit': self.price_unit,
            'tax_ids': [(6, 0, self.tax_ids.ids)],
            'van_order_line_id': self.id,
            'promotion_id': self.promotion_id.id,
            'promotion_account_id': self.promotion_account_id.id,
            'company_id': self.order_id.company_id.id,
        }