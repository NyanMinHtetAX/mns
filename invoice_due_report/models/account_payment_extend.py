import json
from odoo import models, fields, api, tools
from odoo.fields import Date
from datetime import timedelta


class CustomAccountPayment(models.Model):
    _inherit = 'account.payment'  # Inherit from the existing account.payment model

    payment_date = fields.Date(string='Payment Date', compute="_get_payment_date", store=True)

    def _get_payment_date(self):
        for rec in self:
            rec.payment_date = rec.date