# -*- coding: utf-8 -*-
import datetime
from odoo import api, fields, models, tools, _


class ProductCategory(models.Model):
    '''
        add customized fields
    '''
    _inherit = "product.category"

    code = fields.Char('Category Code')

    _sql_constraints = [('unique_code', 'unique(code)', 'Cannot create duplicate Code!')]
