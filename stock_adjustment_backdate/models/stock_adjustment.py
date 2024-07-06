from odoo import api, models, fields, _
from odoo.exceptions import UserError
from datetime import datetime
from dateutil.relativedelta import relativedelta


STATES = [('draft', 'Draft'),
          ('confirm', 'In Progress'),
          ('done', 'Done'),
          ('cancel', 'Cancelled')]


class StockAdjustment(models.Model):

    _name = 'stock.adjustment'
    _description = 'Stock Adjustment'
    _order = 'date desc, id desc'

    name = fields.Char('Name', required=1, default='Draft')
    description = fields.Char('Description',
                              required=1,
                              default=lambda self: f'Adjustment - {fields.Date.context_today(self).strftime("%d/%m/%Y")}')
    date = fields.Datetime('Date', default=fields.Datetime.now)
    location_ids = fields.Many2many('stock.location',
                                    'adjustment_location_rel',
                                    'adjustment_id',
                                    'location_id',
                                    'Locations', domain=[('usage', '=', 'internal')])
    product_ids = fields.Many2many('product.product',
                                   'adjustment_product_rel',
                                   'adjustment_id',
                                   'product_id',
                                   'Products', domain=[('detailed_type', '=', 'product')])
    counted_qty_type = fields.Selection([('on_hand', 'Default to Stock On Hand'),
                                         ('zero', 'Default to Zero')], 'Counted Qty', default='on_hand', required=1)
    company_id = fields.Many2one('res.company', 'Company', default=lambda self: self.env.company.id)
    move_ids = fields.One2many('stock.move', 'adjustment_id', 'Stock Moves')
    line_ids = fields.One2many('stock.adjustment.line', 'adjustment_id', 'Lines')
    state = fields.Selection(STATES, default='draft')

    def btn_start(self):
        self.write({
            'name': self.env['ir.sequence'].sudo().next_by_code('adjustment.seq'),
            'state': 'confirm',
        })
        return self.open_adjustment_lines()

    def btn_continue(self):
        return self.open_adjustment_lines()

    def btn_validate(self):
        lines = self.line_ids.filtered(lambda l: l.difference_qty != 0)
        if not lines:
            raise UserError('There is nothing to validate.')
        for line in lines:
            inventory_location = line.product_id.with_company(self.company_id.id).property_stock_inventory.id
            if line.difference_qty > 0:
                move = self.env['stock.move'].create(line._prepare_move_values(line.difference_qty,
                                                                               inventory_location,
                                                                               line.location_id.id))
            else:
                move = self.env['stock.move'].create(line._prepare_move_values(abs(line.difference_qty),
                                                                               line.location_id.id,
                                                                               inventory_location))
            line.move_id = move.id
        self.move_ids.filtered(lambda move: move.state != 'done').with_context(force_period_date=self.date)._action_done()
        self.move_ids.write({'date': self.date})
        self.move_ids.move_line_ids.write({'date': self.date})
        self.write({'state': 'done'})
        return True

    def btn_cancel(self):
        self.state = 'cancel'

    def open_adjustment_lines(self):
        ctx = {'default_adjustment_id': self.id}
        if len(self.product_ids) == 1:
            ctx.update({'default_product_id': self.product_ids[0].id})
        if self.location_ids:
            ctx.update({'default_location_id': self.location_ids[0].id})
        return {
            'name': 'Inventory Lines',
            'type': 'ir.actions.act_window',
            'res_model': 'stock.adjustment.line',
            'view_mode': 'tree,form',
            'domain': [('adjustment_id', '=', self.id)],
            'context': ctx,
        }

    def btn_show_product_moves(self):
        action = self.env['ir.actions.act_window']._for_xml_id('stock.stock_move_line_action')
        action['domain'] = [('move_id', 'in', self.move_ids.ids)]
        return action

    def unlink(self):
        for rec in self:
            if rec.state not in ['draft', 'cancel']:
                raise UserError('You can only delete draft or cancelled records.')
        return super(StockAdjustment, self).unlink()

    @api.constrains('date')
    def check_inventory_date_order(self):
        for stock_adjustment in self:
            date = stock_adjustment.date
            if not date:
                continue
            today = fields.Date.today()
            user = self.env.user
            date = stock_adjustment.date.date()
            inventory_allow_back_date = user.inventory_allow_back_date
            inventory_back_days = user.inventory_back_days or 0
            backdate_limit = today - relativedelta(days=inventory_back_days)
            if date < today and (not inventory_allow_back_date or date < backdate_limit):
                raise UserError(_('You are not allowed to do backdate transaction or your backdate is beyond limit (ADJ).'))


class StockAdjustmentLine(models.Model):

    _name = 'stock.adjustment.line'
    _description = 'Stock Adjustment Line'

    @api.onchange('adjustment_id')
    def get_product_domain(self):
        product_domain = [('detailed_type', '=', 'product')]
        location_domain = [('usage', '=', 'internal')]
        if self.adjustment_id:
            if self.adjustment_id.product_ids:
                product_domain.append(
                    ('id', 'in', self.adjustment_id.product_ids.ids)
                )
            if self.adjustment_id.location_ids:
                location_domain.append(
                    ('id', 'in', self.adjustment_id.location_ids.ids)
                )
        return {'domain': {'product_id': product_domain, 'location_id': location_domain}}

    product_id = fields.Many2one('product.product', 'Product', required=1)
    location_id = fields.Many2one('stock.location', 'Location', required=1)
    adjustment_id = fields.Many2one('stock.adjustment', 'Adjustment', required=1, ondelete='cascade', copy=False)
    date = fields.Datetime('Date', related='adjustment_id.date', store=True)
    origin = fields.Char('Ref', related='adjustment_id.name', store=True)
    theoretical_qty = fields.Float('Theoretical Qty', compute='_compute_on_hand_at_date', store=True)
    product_qty = fields.Float('Product Qty', required=1)
    difference_qty = fields.Float('Difference Qty', compute='_compute_difference_qty', store=True)
    state = fields.Selection(related='adjustment_id.state', store=True)
    move_id = fields.Many2one('stock.move', 'Stock Move')

    _sql_constraints = [
        (
            'unique_line',
            'unique(product_id, location_id, adjustment_id)',
            'Line with the same product and location already exists.'
            'Please update the existing line instead of creating new one.',
        ),
    ]

    def calculate_qty_with_date(self, date, product, location, operator):
        locations = self.env['stock.location'].sudo().search([('location_id', '=', location.id)])
        locations |= location
        out_moves = self.env['stock.move.line'].sudo().search([('product_id', '=', product.id),
                                                               ('location_id.usage', '=', 'internal'),
                                                               ('location_id', 'in', locations.ids),
                                                               ('date', operator, date),
                                                               ('state', '=', 'done')])
        in_moves = self.env['stock.move.line'].sudo().search([('product_id', '=', product.id),
                                                              ('location_dest_id.usage', '=', 'internal'),
                                                              ('location_dest_id', 'in', locations.ids),
                                                              ('date', operator, date),
                                                              ('state', '=', 'done')])
        qty = sum(in_moves.mapped('qty_done')) - sum(out_moves.mapped('qty_done'))
        return qty

    @api.depends('product_id', 'location_id')
    def _compute_on_hand_at_date(self):
        for rec in self:
            if not rec.product_id or not rec.location_id:
                rec.theoretical_qty = 0
                continue
            rec.theoretical_qty = self.calculate_qty_with_date(rec.date, rec.product_id, rec.location_id, '<')

    @api.onchange('product_id', 'location_id', 'adjustment_id')
    def calculate_line_on_hand_qty(self):
        on_hand_qty = 0
        if self.adjustment_id.counted_qty_type == 'on_hand' and self.product_id and self.location_id:
            on_hand_qty = self.calculate_qty_with_date(self.date, self.product_id, self.location_id, '<')
        self.product_qty = on_hand_qty if on_hand_qty >= 0 else 0

    @api.depends('product_qty', 'theoretical_qty')
    def _compute_difference_qty(self):
        for rec in self:
            rec.difference_qty = rec.product_qty - rec.theoretical_qty

    def _prepare_move_values(self, qty, location_id, location_dest_id):
        self.ensure_one()
        return {
            'name': 'INV:' + self.adjustment_id.name,
            'product_id': self.product_id.id,
            'product_uom': self.product_id.uom_id.id,
            'product_uom_qty': qty,
            'date': self.date,
            'company_id': self.adjustment_id.company_id.id,
            'origin': self.adjustment_id.name,
            'adjustment_id': self.adjustment_id.id,
            'state': 'confirmed',
            'location_id': location_id,
            'location_dest_id': location_dest_id,
            'move_line_ids': [(0, 0, {
                'product_id': self.product_id.id,
                'product_uom_qty': 0,
                'product_uom_id': self.product_id.uom_id.id,
                'qty_done': qty,
                'location_id': location_id,
                'location_dest_id': location_dest_id,
            })]
        }
