from odoo import api, models, fields, _
from odoo.exceptions import UserError
from datetime import datetime
from dateutil.relativedelta import relativedelta

class Picking(models.Model):
    _inherit = "stock.picking"

    # close constrain method and use with button_validate() by ETK
    def button_validate(self):
        res = super(Picking, self).button_validate()
        for stock_picking in self:
            scheduled_date = datetime.strptime(stock_picking.scheduled_date.strftime('%Y-%m-%d'), '%Y-%m-%d').date()
            if not scheduled_date:
                continue
            user = self.env.user
            inventory_allow_lock_date = user.inventory_allow_lock_date
            inventory_lock_date = user.inventory_lock_date or ''
            if inventory_allow_lock_date and scheduled_date <= inventory_lock_date:
                raise UserError(_('You are not allowed because your order date is beyond lock date limit.'))
            else:
                continue
        return res


    # @api.constrains('scheduled_date')
    # def check_date_order(self):
    #     for stock_picking in self:
    #         scheduled_date = datetime.strptime(stock_picking.scheduled_date.strftime('%Y-%m-%d'), '%Y-%m-%d').date()
    #         if not scheduled_date:
    #             continue
    #         user = self.env.user
    #         inventory_allow_lock_date = user.inventory_allow_lock_date
    #         inventory_lock_date = user.inventory_lock_date or ''
    #         if inventory_allow_lock_date and scheduled_date <= inventory_lock_date:
    #             raise UserError(_('You are not allowed because your order date is beyond lock date limit.'))
    #         else:
    #             continue
