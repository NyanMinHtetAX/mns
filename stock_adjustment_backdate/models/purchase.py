from odoo import api, models, fields, _
from odoo.exceptions import UserError
from datetime import datetime
from dateutil.relativedelta import relativedelta


class PurchaseOrder(models.Model):

    _inherit = 'purchase.order'

    @api.onchange('date_order')
    def _onchange_date(self):
        if self.date_order:
            self.date_planned = self.date_order

    def button_approve(self, force=False):
        res = super(PurchaseOrder, self).button_approve(force=force)
        self.write({
            'date_planned': self.date_order,
            'date_approve': self.date_order,
        })
        return res

    def _prepare_invoice(self):
        values = super(PurchaseOrder, self)._prepare_invoice()
        values.update({
            'invoice_date': self.date_order,
            'date': self.date_order,
        })
        return values

    def button_confirm(self):
        res = super(PurchaseOrder, self).button_confirm()
        self.check_date_order()
        return res

    @api.constrains('date_order')
    def check_date_order(self):
        for order in self:
            order_date = datetime.strptime(order.date_order.strftime('%Y-%m-%d'), '%Y-%m-%d').date()
            if not order_date:
                continue
            today = fields.Date.today()
            user = self.env['res.users'].browse(self.env.context.get('uid'))
            po_allow_back_date = user.po_allow_back_date
            po_back_days = user.po_back_days or 0
            backdate_limit = today - relativedelta(days=po_back_days)
            if order_date < today and (not po_allow_back_date or order_date < backdate_limit):
                raise UserError(_('You are not allowed to do backdate transaction or your backdate is beyond limit(PO).'))

