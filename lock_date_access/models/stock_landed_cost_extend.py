from odoo import api, models, fields, _
from odoo.exceptions import UserError
from datetime import datetime
from dateutil.relativedelta import relativedelta

class StockLandedCost(models.Model):

    _inherit = 'stock.landed.cost'

    @api.constrains('date')
    def check_date_order(self):
        for stock_scrap in self:
            date = stock_scrap.date
            if not date:
                continue
            user = self.env.user
            inventory_allow_lock_date = user.inventory_allow_lock_date
            inventory_lock_date = user.inventory_lock_date or ''
            if inventory_allow_lock_date and date < inventory_lock_date:
                raise UserError(_('You are not allowed because your order date is beyond lock date limit.'))
            else:
                continue
