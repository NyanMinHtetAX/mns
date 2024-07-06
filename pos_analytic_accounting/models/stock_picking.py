from odoo import api, models, fields


class StockPicking(models.Model):

    _inherit = 'stock.picking'

    @api.model
    def _create_picking_from_pos_order_lines(self, location_dest_id, lines, picking_type, partner=False):
        self = self.with_context(analytic_account_id=lines.order_id.analytic_account_id.id)
        pickings = super(StockPicking, self)._create_picking_from_pos_order_lines(location_dest_id,
                                                                                  lines,
                                                                                  picking_type,
                                                                                  partner)
        analytic_account_id = lines.order_id.analytic_account_id
        pickings.write({'analytic_account_id': analytic_account_id})
        return pickings

    def _prepare_picking_vals(self, partner, picking_type, location_id, location_dest_id):
        values = super(StockPicking, self)._prepare_picking_vals(partner,
                                                                 picking_type,
                                                                 location_id,
                                                                 location_dest_id)
        analytic_account_id = self.env.context.get('analytic_account_id', False)
        if analytic_account_id:
            values['analytic_account_id'] = analytic_account_id
        return values

    def _prepare_stock_move_vals(self, first_line, order_lines):
        values = super(StockPicking, self)._prepare_stock_move_vals(first_line, order_lines)
        values['analytic_account_id'] = first_line.order_id.analytic_account_id.id
        return values
