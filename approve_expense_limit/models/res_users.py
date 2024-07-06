from odoo import api, models, fields, _


class ResUsers(models.Model):
    _inherit = 'res.users'

    is_limit_expense = fields.Boolean('Limited Expense')
    limit_expense_amount = fields.Float('Amount')
