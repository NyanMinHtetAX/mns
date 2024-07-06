from odoo import models, fields


class Religion(models.Model):

    _name = 'res.religion'
    _description = 'Religion'

    name = fields.Char(string='Name', required=True)
