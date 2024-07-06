from odoo import models, fields


class ResUsers(models.Model):
    _inherit = 'res.users'

    so_allow_back_date = fields.Boolean('Allow Sale Order Back Date?')
    so_back_days = fields.Integer('Sale Order Backdate Limits(Days)')

    po_allow_back_date = fields.Boolean('Allow Purchase Order Back Date?')
    po_back_days = fields.Integer('Purchase Order Backdate Limit(Days)')

    inventory_allow_back_date = fields.Boolean("Allow Inventory Back Date?")
    inventory_back_days = fields.Integer('Inventory Backdate Limits(Days)')

    invoice_allow_back_date = fields.Boolean('Allow Invoice Back Date?')
    invoice_back_days = fields.Integer('Invoice Backdate Limits(Days)')