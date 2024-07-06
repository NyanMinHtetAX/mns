from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.tools import float_compare


class StockMultiScrap(models.Model):

    _name = 'stock.multi.scrap'
    _description = 'Stock Multi Scrap'

    name = fields.Char('Reference',
                       default=lambda self: _('New'),
                       copy=False,
                       readonly=True,
                       required=True,
                       states={'done': [('readonly', True)]})
    document_number = fields.Char(string='Document Number',
                                  states={'done': [('readonly', True)]})
    excepted_date = fields.Datetime(string='Excepted Date',
                                    states={'done': [('readonly', True)]},
                                    required=True,
                                    default=lambda self: fields.datetime.now())
    line_ids = fields.One2many('stock.multi.scrap.line', 'multi_scrap_id',
                               string='Multi Scrap Lines',
                               states={'done': [('readonly', True)]})
    picking_id = fields.Many2one('stock.picking', 'Picking',
                                 states={'done': [('readonly', True)]})
    analytic_account_id = fields.Many2one('account.analytic.account', 'Analytic Account')
    state = fields.Selection([('draft', 'Draft'), ('done', 'Done')],
                             string='Status',
                             default="draft")
    sale_man_id = fields.Many2one('res.users', 'Sales Man', default=lambda self: self.env.user.id)
    team_id = fields.Many2one('crm.team', 'Sales Team', domain=[('is_van_team', '=', True)])
    is_van_scrap = fields.Boolean('Is Van Scrap')
    company_id = fields.Many2one('res.company', 'Company', default=lambda self: self.env.company.id, required=1)

    @api.model
    def create(self, vals):
        if 'name' not in vals or vals['name'] == _('New'):
            if vals.get('is_van_scrap'):
                vals['name'] = self.env['ir.sequence'].next_by_code('stock.multi.scrap.van') or _('New')
            else:
                vals['name'] = self.env['ir.sequence'].next_by_code('stock.multi.scrap') or _('New')
        res = super(StockMultiScrap, self).create(vals)
        return res

    def do_scrap(self):
        for scrap in self.line_ids:
            scrap.do_scrap()
        return self.write({'state': 'done'})

    def action_validate(self):
        self.ensure_one()
        for line in self.line_ids:
            if line.product_id.type != 'product':
                return self.do_scrap()
            precision = self.env['decimal.precision'].precision_get('Product Unit of Measure')
            available_qty = sum(self.env['stock.quant']._gather(line.product_id,
                                                                line.location_id,
                                                                line.lot_id,
                                                                strict=True).mapped('quantity'))

            scrap_qty = line.product_uom_id._compute_quantity(line.scrap_qty, line.product_id.uom_id)
            if float_compare(available_qty, scrap_qty, precision_digits=precision) >= 0:
                return self.do_scrap()
            else:
                return {
                    'name': _('Insufficient Quantity'),
                    'view_type': 'form',
                    'view_mode': 'form',
                    'res_model': 'stock.warn.insufficient.qty.scrap.multi',
                    'view_id': self.env.ref('stock_multi_scrap.stock_warn_insufficient_qty_scrap_form_view_multi').id,
                    'type': 'ir.actions.act_window',
                    'context': {
                        'default_product_id': line.product_id.id,
                        'default_location_id': line.location_id.id,
                        'default_multi_scrap_id': self.id,
                        'default_multi_line_id': line.id
                    },
                    'target': 'new'
                }
        return self.write({'state': 'done'})

    def unlink(self):
        if 'done' in self.mapped('state'):
            raise UserError(_('You cannot delete a scrap which is done.'))
        return super(StockMultiScrap, self).unlink()

    def btn_show_product_moves(self):
        move_ids = self.line_ids.move_id.ids
        return {
            'name': 'Product Moves',
            'type': 'ir.actions.act_window',
            'res_model': 'stock.move.line',
            'view_mode': 'tree,form',
            'domain': [('move_id', 'in', move_ids)],
        }


class StockMultiScrapLine(models.Model):

    _name = 'stock.multi.scrap.line'
    _description = 'Multi Scrap Line'

    def _get_default_scrap_location_id(self):
        return self.env['stock.location'].search([('scrap_location', '=', True),
                                                  ('company_id', 'in', [self.env.user.company_id.id, False])],
                                                 limit=1).id

    def _get_default_location_id(self):
        company_user = self.env.user.company_id
        warehouse = self.env['stock.warehouse'].search([('company_id', '=', company_user.id)], limit=1)
        if warehouse:
            return warehouse.lot_stock_id.id
        return None

    product_id = fields.Many2one('product.product', 'Product',
                                 domain=[('type', 'in', ['product', 'consu'])],
                                 required=True)
    lot_id = fields.Many2one('stock.production.lot', 'Lot/Serial Number',
                             domain="[('product_id', '=', product_id)]")
    scrap_qty = fields.Float('Scrap Quantity',
                             default=1.0,
                             required=True,
                             compute='compute_multi_uom_scrap_qty',
                             inverse='set_multi_uom_scrap_qty',
                             store=True)
    product_uom_id = fields.Many2one('uom.uom', 'Unit of Measure',
                                     required=True)
    location_id = fields.Many2one('stock.location', 'Source Location',
                                  domain="[('usage', '=', 'internal')]",
                                  required=True,
                                  default=False)
    scrap_location_id = fields.Many2one('stock.location', 'Scrap Location',
                                        default=_get_default_scrap_location_id,
                                        domain="[('scrap_location', '=', True)]",
                                        required=True)
    remark = fields.Char('Remark')
    multi_scrap_id = fields.Many2one('stock.multi.scrap', string='Multi Scrap')
    picking_id = fields.Many2one('stock.picking', 'Picking')
    move_id = fields.Many2one('stock.move', 'Scrap Move', readonly=True)
    state = fields.Selection(related='multi_scrap_id.state', string='Status', copy=False, store=True)
    date = fields.Datetime(string='Date', related='multi_scrap_id.excepted_date')
    analytic_account_id = fields.Many2one('account.analytic.account', 'Analytic Account',
                                          related='multi_scrap_id.analytic_account_id', store=True)
    multi_uom_line_id = fields.Many2one('multi.uom.line', 'Multi UoM Line')
    multi_uom_qty = fields.Float('Multi UoM Quantity', default=1.0, required=True, digits='Product Unit of Measure')
    multi_uom_line_ids = fields.Many2many('multi.uom.line', compute='compute_multi_uom_line_ids')
    van_location_id = fields.Many2one('stock.location', compute='compute_van_location')

    @api.onchange('picking_id')
    def _onchange_picking_id(self):
        if self.picking_id:
            self.location_id = (self.picking_id.state == 'done') and \
                               self.picking_id.location_dest_id.id or self.picking_id.location_id.id

    @api.onchange('product_id')
    def onchange_product_id(self):
        if self.product_id:
            self.product_uom_id = self.product_id.uom_id.id
        line = self.product_id.multi_uom_line_ids.filtered(lambda l: l.uom_id.id == self.product_id.uom_id.id)
        self.multi_uom_line_id = line.id

    def _get_origin_moves(self):
        return self.picking_id and self.picking_id.move_lines.filtered(lambda x: x.product_id == self.product_id)

    def action_get_stock_picking(self):
        action = self.env.ref('stock.action_picking_tree_all').read([])[0]
        action['domain'] = [('id', '=', self.picking_id.id)]
        return action

    def _prepare_move_values(self):
        self.ensure_one()
        return {
                'name': self.multi_scrap_id.name,
                'product_id': self.product_id.id,
                'product_uom': self.product_uom_id.id,
                'product_uom_qty': self.scrap_qty,
                'date': self.multi_scrap_id.excepted_date,
                'location_id': self.location_id.id,
                'scrapped': True,
                'location_dest_id': self.scrap_location_id.id,
                # 'multi_scrap_analytic_acc_id': self.analytic_account_id.id,
                'multi_uom_line_id': self.multi_uom_line_id.id,
                'move_line_ids': [(0, 0, {'product_id': self.product_id.id,
                                          'product_uom_id': self.product_uom_id.id,
                                          'qty_done': self.scrap_qty,
                                          'location_id': self.location_id.id,
                                          'date': self.multi_scrap_id.excepted_date,
                                          'location_dest_id': self.scrap_location_id.id,
                                          'lot_id': self.lot_id.id, })],
        }

    def do_scrap(self):
        for scrap in self:
            move = self.env['stock.move'].create(scrap._prepare_move_values())
            move.move_line_ids.update({
                'lot_id': self.lot_id.id
            })
            move.with_context(is_scrap=True, force_period_date=self.multi_scrap_id.excepted_date)._action_done()
            scrap.write({'move_id': move.id, 'state': 'done'})
        return True

    def action_get_stock_move_lines(self):
        for res in self.move_id:
            res.date = self.date
            res.move_line_ids.date = self.date
        action = self.env.ref('stock.stock_move_line_action').read([])[0]
        action['domain'] = [('move_id', '=', self.move_id.id)]
        return action

    @api.depends('multi_uom_line_id', 'multi_uom_qty')
    def compute_multi_uom_scrap_qty(self):
        for rec in self:
            rec.scrap_qty = rec.multi_uom_qty * rec.multi_uom_line_id.ratio

    def set_multi_uom_scrap_qty(self):
        for rec in self:
            if rec.multi_uom_line_id:
                rec.multi_uom_qty = rec.scrap_qty / rec.multi_uom_line_id.ratio
            else:
                rec.multi_uom_qty = rec.scrap_qty

    @api.depends('product_id')
    def compute_multi_uom_line_ids(self):
        for rec in self:
            rec.multi_uom_line_ids = rec.product_id.multi_uom_line_ids.ids

    @api.depends('multi_scrap_id.team_id')
    def compute_van_location(self):
        for line in self:
            line.van_location_id = line.multi_scrap_id.team_id.van_location_id.id
