from odoo import models, fields, api, _
from dateutil.relativedelta import relativedelta
from datetime import datetime


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    to_thirty_days = fields.Integer(string='0-30', compute='_get_duration_of_no_active', store=True)
    to_sixty_days = fields.Integer(string='31-60', compute='_get_duration_of_no_active', store=True)
    to_ninety_days = fields.Integer(string='61-90', compute='_get_duration_of_no_active', store=True)
    to_one_twenty_days = fields.Integer(string='91-120', compute='_get_duration_of_no_active', store=True)
    to_older_days = fields.Integer(string='Older', compute='_get_duration_of_no_active', store=True)

    @api.depends('date_approve')
    def _get_duration_of_no_active(self):
        for rec in self:
            if rec.date_approve:
                now = datetime.now() + relativedelta(hours=6, minutes=30)
                approve = rec.date_approve + relativedelta(hours=6, minutes=30)
                duration = (now - approve).days
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

