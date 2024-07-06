from re import M
from odoo import api, models, fields


class User(models.Model):

    _inherit = 'res.users'

    fs_signature = fields.Image('Signature')
