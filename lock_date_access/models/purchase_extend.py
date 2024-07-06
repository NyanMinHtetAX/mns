from odoo import api, models, fields, _
from odoo.exceptions import UserError
from datetime import datetime
from dateutil.relativedelta import relativedelta

class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    @api.constrains('date_order')
    def check_date_order(self):
        for order in self:
            order_date = datetime.strptime(order.date_order.strftime('%Y-%m-%d'), '%Y-%m-%d').date()
            if not order_date:
                continue
            user = self.env.user
            po_allow_lock_date = user.po_allow_lock_date
            po_lock_date = user.po_lock_date or ''
            if po_allow_lock_date and order_date <= po_lock_date:
                raise UserError(_('You are not allowed because your order date is beyond lock date limit.'))
            else:
                continue
