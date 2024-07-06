from odoo import api, models, fields, _
from odoo.exceptions import UserError
from datetime import datetime
from dateutil.relativedelta import relativedelta

class StockMultiScrap(models.Model):

    _inherit = 'stock.multi.scrap'

    @api.constrains('excepted_date')
    def check_date_order(self):
        for stock_scrap in self:
            excepted_date = datetime.strptime(stock_scrap.excepted_date.strftime('%Y-%m-%d'), '%Y-%m-%d').date()
            if not excepted_date:
                continue
            user = self.env.user
            inventory_allow_lock_date = user.inventory_allow_lock_date
            inventory_lock_date = user.inventory_lock_date or ''
            if inventory_allow_lock_date and excepted_date < inventory_lock_date:
                raise UserError(_('You are not allowed because your order date is beyond lock date limit.'))
            else:
                continue
