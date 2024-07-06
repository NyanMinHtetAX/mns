from odoo import models, fields, api, _
from dateutil.relativedelta import relativedelta
from datetime import datetime


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    to_thirty_days = fields.Integer(string='0-30', compute='_get_duration_of_no_active', store=True)
    to_sixty_days = fields.Integer(string='31-60', compute='_get_duration_of_no_active', store=True)
    to_ninety_days = fields.Integer(string='61-90', compute='_get_duration_of_no_active', store=True)
    to_one_twenty_days = fields.Integer(string='91-120', compute='_get_duration_of_no_active', store=True)
    to_older_days = fields.Integer(string='Older', compute='_get_duration_of_no_active', store=True)

    @api.depends('date_order')
    def _get_duration_of_no_active(self):
        for rec in self:
            if rec.date_order:
                now = datetime.now() + relativedelta(hours=6, minutes=30)
                order_date = rec.date_order + relativedelta(hours=6, minutes=30)
                duration = (now - order_date).days
                if 31 > duration > 0:
                    rec.to_thirty_days = duration
                elif 61 > duration > 30:
                    rec.to_sixty_days = duration
                elif 91 > duration > 60:
                    rec.to_ninety_days = duration
                elif 121 > duration > 90:
                    rec.to_one_twenty_days = duration
                else:
                    rec.to_older_days = duration

