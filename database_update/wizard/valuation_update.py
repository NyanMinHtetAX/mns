from odoo import models, fields, api, _
from odoo.exceptions import UserError
from datetime import datetime, timedelta
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT


class StockValuationUpdate(models.Model):
    _name = 'stock.valuation.update'
    _description = 'Stock Valuation Update Date'

    date = fields.Datetime('Update Date', required=True)

    def apply_update_date(self):
        selected_lines = self._context.get('active_ids')
        valuation_lines = self.env['stock.valuation.layer'].browse(selected_lines)

        for line in valuation_lines:
            line.write({
                'date': self.date,
            })

        date = datetime.strptime(str(self.date), DEFAULT_SERVER_DATETIME_FORMAT)
