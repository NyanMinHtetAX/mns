from odoo import models, fields, api, _


class PartnerClass(models.Model):
    _name = "partner.class"
    _description = "Customer Class"

    name = fields.Char(string='Name')

    _sql_constraints = [('unique_name', 'unique(name)', 'Cannot create duplicate Name!')]


