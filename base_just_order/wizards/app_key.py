# -*- coding: utf-8 -*-

import math
import re
from odoo import api, models, fields, _
from odoo.exceptions import ValidationError
import random
import string
from odoo.exceptions import ValidationError, UserError

class AppKey(models.Model):
    _name = 'app.key'
    _description = "App Key"

    def _get_key(self):
        jr_data = self.env['jr.config'].search([])
        for i in jr_data:
            if i.key:
                return i.key
            else:
                return ''
    key = fields.Char(string='Key',default=_get_key)

    def store_in_jr(self):
        jr_data = self.env['jr.config'].search([])
        for i in jr_data:
            i.key = self.key



