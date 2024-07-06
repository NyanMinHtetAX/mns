from odoo import api, models, fields, _
from odoo.exceptions import UserError
from datetime import datetime
from dateutil.relativedelta import relativedelta

class SaleOrder(models.Model):

    _inherit = 'sale.order'

    @api.constrains('date_order')
    def check_date_order(self):
        for order in self:
            order_date = datetime.strptime(order.date_order.strftime('%Y-%m-%d'), '%Y-%m-%d').date()
            if not order_date:
                continue
            user = self.env.user
            so_allow_lock_date = user.so_allow_lock_date
            so_lock_date = user.so_lock_date or ''
            if so_allow_lock_date and order_date <= so_lock_date:
                raise UserError(_('You are not allowed because your order date is beyond lock date limit.'))
            else:
                continue

    def write(self, vals):
        res = super(SaleOrder, self).write(vals)
        for order in self:
            order_date = datetime.strptime(order.date_order.strftime('%Y-%m-%d'), '%Y-%m-%d').date()
            if not order_date:
                continue
            user = self.env.user
            so_allow_lock_date = user.so_allow_lock_date
            so_lock_date = user.so_lock_date or ''
            if so_allow_lock_date and order_date <= so_lock_date:
                raise UserError(_('You are not allowed because your order date is beyond lock date limit.'))
            else:
                continue
        return res
