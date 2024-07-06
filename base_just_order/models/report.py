from odoo import models, fields


class Report(models.Model):
    _name = 'jr.report'
    _description = 'Just Order Report'

    name = fields.Char(string='Report Name')
