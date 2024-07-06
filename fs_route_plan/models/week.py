from odoo import api, models, fields


class Week(models.Model):

    _name = 'week.week'
    _description = 'Route Plan Week'

    name = fields.Char('Name')
