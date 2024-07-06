# -*- coding: utf-8 -*-
import datetime

from odoo import api, fields, models, tools, exceptions, _

import itertools
import psycopg2

from odoo.addons import decimal_precision as dp

from odoo import api, fields, models, tools, _
from odoo.exceptions import ValidationError, RedirectWarning, except_orm
from odoo.tools import pycompat


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    brand_id = fields.Many2one('product.brand', string="Brand Name")
    brand_owner = fields.Many2many('res.partner', string='Brand Owner', domain=[('supplier', '=', True)])
    standard_price = fields.Float(
        'Cost', compute='_compute_standard_price', tracking=True,
        inverse='_set_standard_price', search='_search_standard_price',
        digits='Product Price', groups="base.group_user",
        help="""In Standard Price & AVCO: value of the product (automatically computed in AVCO).
              In FIFO: value of the next unit that will leave the stock (automatically computed).
              Used to value the product when the purchase cost is not known (e.g. inventory adjustment).
              Used to compute margins on sale orders.""")
    company_id = fields.Many2one(
        'res.company', 'Company', index=1, tracking=True)


    def generate_default_code(self):
        for line in self:
            group_code = line.product_group_id.code
            brand_code = line.brand_id.product_brand_code

            obj = self.env['product.sequence'].search([('product_group_id', '=', line.product_group_id.id),
                                                       ('brand_id', '=', line.brand_id.id)])
            if not obj:
                obj = self.env['product.sequence'].create({
                    'sequence': 1,
                    'product_group_id': line.product_group_id.id,
                    'brand_id': line.brand_id.id,

                })

            sr = "{:04d}".format(int(obj.sequence))
            if line.default_code:
                pass
            else:
                if group_code and brand_code and sr:
                    line.default_code = str(group_code) + str(brand_code) + sr
                else:
                    raise exceptions.ValidationError(
                        _('Please Fill Product Brand Code and Product Group Code')
                    )
                obj.write({'sequence': obj.sequence + 1})


class ProductProduct(models.Model):
    '''
        add customized fields
    '''
    _inherit = "product.product"

    def generate_default_code(self):
        for line in self:
            brand_code = line.brand_id.product_brand_code
            group_code = line.product_group_id.product_line_code
            obj = self.env['product.sequence'].search([('product_group_id', '=', line.product_group_id.id),
                                                       ('brand_id', '=', line.brand_id.id)])
            if not obj:
                obj = self.env['product.sequence'].create({
                    'sequence': 1,
                    'product_group_id': self.product_group_id.id,
                    'brand_id': self.brand_id.id,

                })
            sr = "{:04d}".format(int(obj.sequence))
            if line.default_code:
                pass
            else:
                if group_code and brand_code and sr:
                    line.default_code = str(group_code) + str(brand_code) + sr
                else:
                    raise exceptions.ValidationError(
                        _('Please Fill Product Brand Code and Product Group Code')
                    )
                obj.write({'sequence': obj.sequence + 1})


class ProductBrand(models.Model):
    _name = 'product.brand'
    _description = 'product brand'

    name = fields.Char('Name', required=True)
    product_brand_code = fields.Char('Brand Code')

    _sql_constraints = [
        ('name_uniq', 'unique (name)', 'The name of the product brand must be unique !'),
        ('product_brand_code_uniq', 'unique (product_brand_code)', 'The code of the product brand must be unique !')
    ]

    # @api.model
    # def create(self, vals):
    #     product_brand_code = self.env['ir.sequence'].sudo().next_by_code('product.brand')
    #     vals['product_brand_code'] = product_brand_code
    #     return super(ProductBrand, self).create(vals)
