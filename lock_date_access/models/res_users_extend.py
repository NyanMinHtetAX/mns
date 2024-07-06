from odoo import models, fields

class ResUsers(models.Model):

    _inherit = 'res.users'

    so_allow_lock_date = fields.Boolean('SO Allow Lock Date?')
    so_lock_date = fields.Date('SO Allow Limits Date')

    po_allow_lock_date = fields.Boolean('PO Allow Lock Date?')
    po_lock_date = fields.Date('PO Allow Limits Date')

    invoice_allow_lock_date = fields.Boolean('Bill & Invoice Allow Lock Date?')
    invoice_lock_date = fields.Date('Bill & Invoice Allow Limits Date')

    inventory_allow_lock_date = fields.Boolean('Inventory Allow Lock Date?')
    inventory_lock_date = fields.Date('Inventory Allow Limits Date')

