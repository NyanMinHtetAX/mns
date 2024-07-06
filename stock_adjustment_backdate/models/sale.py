import pytz
from odoo import api, models, fields, _
from odoo.exceptions import UserError
from datetime import datetime
from dateutil.relativedelta import relativedelta


class SaleOrder(models.Model):

    _inherit = 'sale.order'

    date_expected = fields.Datetime(string='Backdate',
                                    readonly=True,
                                    required=True,
                                    states={'draft': [('readonly', False)], 'sent': [('readonly', False)]},
                                    default=fields.Datetime.now)

    @api.onchange('date_expected')
    def onchange_backdate(self):
        if self.date_expected:
            self.date_order = self.date_expected

    def _prepare_confirmation_values(self):
        values = super(SaleOrder, self)._prepare_confirmation_values()
        values.update({
            'date_order': self.date_expected,
            'commitment_date': self.date_expected,
        })
        return values

    def _prepare_invoice(self):
        values = super(SaleOrder, self)._prepare_invoice()
        user_tz = pytz.timezone(self.env.user.tz or 'UTC')
        date_expected = self.date_expected.replace(tzinfo=pytz.utc).astimezone(user_tz)
        values.update({
            'invoice_date': date_expected,
            'date': date_expected,
        })
        return values

    @api.constrains('date_order')
    def check_date_order(self):
        for order in self:
            order_date = datetime.strptime(order.date_order.strftime('%Y-%m-%d'), '%Y-%m-%d').date()
            if not order_date:
                continue
            today = fields.Date.today()
            user = self.env['res.users'].browse(self.env.context.get('uid'))
            so_allow_back_date = user.so_allow_back_date
            so_back_days = user.so_back_days or 0
            backdate_limit = today - relativedelta(days=so_back_days)
            if order_date < today and (not so_allow_back_date or order_date < backdate_limit):
                raise UserError(
                    _('You are not allowed to do backdate transaction or your backdate is beyond limit(SO).'))

