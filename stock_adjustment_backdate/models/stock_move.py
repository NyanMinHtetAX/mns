import pytz
from datetime import datetime
from odoo import api, models, fields
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT


class StockMove(models.Model):

    _inherit = 'stock.move'

    adjustment_id = fields.Many2one('stock.adjustment', 'Adjustment')

    def _prepare_common_svl_vals(self):
        res = super(StockMove, self)._prepare_common_svl_vals()
        if self.picking_id:
            res['date'] = self.picking_id.scheduled_date
        elif self.adjustment_id:
            res['date'] = self._context.get('force_period_date')
        elif self.scrapped:
            res['date'] = self._context.get('force_period_date')
        elif self.scrapped:
            res['date'] = self._context.get('force_period_date')
        elif self.is_inventory:
            res['date'] = self._context.get('force_period_date')
        elif self.sale_line_id:
            res['date'] = self.sale_line_id.order_id.date_expected
        elif self.purchase_line_id:
            res['date'] = self.purchase_line_id.order_id.date_order
        else:
            res['date'] = self.date
        return res

    def _prepare_account_move_vals(self,
                                   credit_account_id,
                                   debit_account_id,
                                   journal_id,
                                   qty,
                                   description,
                                   svl_id,
                                   cost):
        values = super(StockMove, self)._prepare_account_move_vals(credit_account_id,
                                                                   debit_account_id,
                                                                   journal_id,
                                                                   qty,
                                                                   description,
                                                                   svl_id,
                                                                   cost)
        local_tz_st = pytz.timezone(self.env.user.tz or 'UTC')
        scheduled_date = self.env.context.get('force_period_date', False)
        if not scheduled_date and (self.picking_id or self.date):
            if self.picking_id:
                scheduled_date = self.picking_id.scheduled_date
            else:
                scheduled_date = self.date
        scheduled_date = scheduled_date.replace(tzinfo=pytz.utc).astimezone(local_tz_st)
        scheduled_date = datetime.strftime(scheduled_date, DEFAULT_SERVER_DATETIME_FORMAT)
        scheduled_date = datetime.strptime(scheduled_date, DEFAULT_SERVER_DATETIME_FORMAT)
        date = scheduled_date.date()
        values.update({'date': date})
        return values

