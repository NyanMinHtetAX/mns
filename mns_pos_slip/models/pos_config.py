from odoo import api, models, fields, _
from datetime import datetime


class PosConfig(models.Model):
    _inherit = 'pos.config'

    logo = fields.Image('Logo')

