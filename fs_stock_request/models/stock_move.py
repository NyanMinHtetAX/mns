from odoo import api, models, fields


class StockMove(models.Model):

    _inherit = 'stock.move'
    lot_ids = fields.Many2many('stock.production.lot', compute='_compute_lot_ids', inverse='_set_lot_ids',
                               string='Serial Numbers',store=True, readonly=False)

    def action_product_forecast_report(self):
        action = super().action_product_forecast_report()
        if self.picking_id.is_requisition or self.picking_id.is_fs_return:
            action['context']['warehouse'] = self.location_id.warehouse_id.id
        return action
