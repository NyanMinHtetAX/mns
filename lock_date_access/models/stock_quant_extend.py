from odoo import api, models, fields, _
from odoo.exceptions import UserError
from datetime import datetime
from dateutil.relativedelta import relativedelta

class StockQuant(models.Model):

    _inherit = 'stock.quant'

    @api.constrains('backdate')
    def check_date_order(self):
        for stock_quant in self:
            backdate = datetime.strptime(stock_quant.backdate.strftime('%Y-%m-%d'), '%Y-%m-%d').date()
            if not backdate:
                continue
            user = self.env.user
            inventory_allow_lock_date = user.inventory_allow_lock_date
            inventory_lock_date = user.inventory_lock_date or ''

            if inventory_allow_lock_date and backdate < inventory_lock_date:
                raise UserError(_('You are not allowed because your order date is beyond lock date limit.'))
            else:
                continue
