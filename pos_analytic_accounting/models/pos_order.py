from odoo import api, models, fields


class PosOrder(models.Model):

    _inherit = 'pos.order'

    analytic_account_id = fields.Many2one('account.analytic.account', 'Analytic Account')

    def _prepare_invoice_line(self, order_line):
        values = super(PosOrder, self)._prepare_invoice_line(order_line)
        values['analytic_account_id'] = order_line.order_id.analytic_account_id.id
        return values

    @api.model
    def _order_fields(self, ui_order):
        values = super(PosOrder, self)._order_fields(ui_order)
        session_id = self.env['pos.session'].browse(ui_order['pos_session_id'])
        values['analytic_account_id'] = session_id.analytic_account_id.id
        return values

    def _prepare_invoice_vals(self):
        values = super(PosOrder, self)._prepare_invoice_vals()
        values['analytic_account_id'] = self.analytic_account_id.id
        return values

    def _create_order_picking(self):
        self.ensure_one()
        if self.to_ship:
            self.lines._launch_stock_rule_from_pos_order_lines()
        else:
            if self._should_create_picking_real_time():
                picking_type = self.config_id.picking_type_id
                if self.partner_id.property_stock_customer:
                    destination_id = self.partner_id.property_stock_customer.id
                elif not picking_type or not picking_type.default_location_dest_id:
                    destination_id = self.env['stock.warehouse']._get_partner_locations()[0].id
                else:
                    destination_id = picking_type.default_location_dest_id.id

                pickings = self.env['stock.picking']._create_picking_from_pos_order_lines(destination_id, self.lines, picking_type, self.partner_id)
                pickings.write({
                    'pos_session_id': self.session_id.id,
                    'pos_order_id': self.id,
                    'origin': self.name,
                    'analytic_account_id': self.session_id.analytic_account_id.id,
                })
