from odoo import api, models, fields, _
from odoo.exceptions import UserError
from datetime import datetime
from dateutil.relativedelta import relativedelta

class StockScrap(models.Model):

    _inherit = 'stock.scrap'

    @api.constrains('date_expected')
    def check_date_order(self):
        for stock_scrap in self:
            date_expected = datetime.strptime(stock_scrap.date_expected.strftime('%Y-%m-%d'), '%Y-%m-%d').date()
            if not date_expected:
                continue
            user = self.env.user
            inventory_allow_lock_date = user.inventory_allow_lock_date
            inventory_lock_date = user.inventory_lock_date or ''

            if inventory_allow_lock_date and date_expected < inventory_lock_date:
                raise UserError(_('You are not allowed because your order date is beyond lock date limit.'))
            else:
                continue
