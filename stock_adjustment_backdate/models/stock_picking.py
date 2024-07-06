import pytz
from datetime import datetime
from odoo.exceptions import UserError
from dateutil.relativedelta import relativedelta
from odoo import api, fields, models, _


class StockPicking(models.Model):

    _inherit = 'stock.picking'

    def _action_done(self):
        res = super(StockPicking, self)._action_done()
        self.write({'date_done': self.scheduled_date, 'priority': '0'})
        self.move_line_ids.write({'date': self.scheduled_date})
        self.move_lines.write({'date': self.scheduled_date})
        return res

    def action_confirm(self):
        res = super().action_confirm()
        for picking in self:
            scheduled_date = datetime.strptime(picking.scheduled_date.strftime('%Y-%m-%d'), '%Y-%m-%d').date()
            if not scheduled_date:
                continue
            today = fields.date.today()
            user = self.env['res.users'].browse(self.env.context.get('uid'))
            inventory_allow_back_date = user.inventory_allow_back_date
            inventory_back_days = user.inventory_back_days or 0
            backdate_limit = today - relativedelta(days=inventory_back_days)
            if scheduled_date < today and (not inventory_allow_back_date or scheduled_date < backdate_limit):
                raise UserError(
                    _('You are not allowed to do backdate transaction or your backdate is picking beyond limit(Picking).'))
        return res

    def button_validate(self):
        res = super().button_validate()
        for picking in self:
            scheduled_date = datetime.strptime(picking.scheduled_date.strftime('%Y-%m-%d'), '%Y-%m-%d').date()
            if not scheduled_date:
                continue
            today = fields.date.today()
            user = self.env['res.users'].browse(self.env.context.get('uid'))
            inventory_allow_back_date = user.inventory_allow_back_date
            inventory_back_days = user.inventory_back_days or 0
            backdate_limit = today - relativedelta(days=inventory_back_days)
            if scheduled_date < today and (not inventory_allow_back_date or scheduled_date < backdate_limit):
                raise UserError(
                    _('You are not allowed to do backdate transaction or your backdate is picking beyond limit (Picking).'))
        return res

