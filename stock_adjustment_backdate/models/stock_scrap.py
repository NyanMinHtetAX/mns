import pytz
from datetime import datetime
from odoo.exceptions import UserError
from dateutil.relativedelta import relativedelta
from odoo import api, fields, models, _


class StockScrap(models.Model):

    _inherit = 'stock.scrap'

    date_expected = fields.Datetime('Expected Date', default=fields.Datetime.now)

    def do_scrap(self):
        self._check_company()
        for scrap in self:
            scrap.name = self.env['ir.sequence'].next_by_code('stock.scrap') or _('New')
            move = self.env['stock.move'].create(scrap._prepare_move_values())
            move.with_context(is_scrap=True, force_period_date=self.date_expected)._action_done()
            move.write({'date': self.date_expected})
            move.move_line_ids.write({'date': self.date_expected})
            scrap.write({'move_id': move.id, 'state': 'done'})
            scrap.date_done = self.date_expected
        return True

    @api.constrains('date_expected')
    def check_inventory_date_order(self):
        for stock_scrap in self:
            date_expected = stock_scrap.date_expected
            if not date_expected:
                continue
            today = fields.date.today()
            user = self.env.user
            date_expected = stock_scrap.date_expected.date()
            inventory_allow_back_date = user.inventory_allow_back_date
            inventory_back_days = user.inventory_back_days or 0
            backdate_limit = today - relativedelta(days=inventory_back_days)
            if date_expected < today and (not inventory_allow_back_date or date_expected < backdate_limit):
                raise UserError(_('You are not allowed to do backdate transaction or your backdate is beyond limit(Scrap).'))
