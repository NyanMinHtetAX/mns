from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    is_delivery = fields.Boolean(default=False, string="Is Delivery")
    is_special_discount = fields.Boolean(default=False, string="Is Special")
    is_down_payment = fields.Boolean(default=False, string="Is Down Payment")

    def product_name_is_already_existing(self, product_name):
        existing_count = self.env['product.template'].search_count([('name', '=', product_name), ('id', '!=', self.id)])
        return product_name in ['DELIVERY CHARGES', 'DOWN PAYMENTS', 'DISCOUNTS'] and existing_count > 0

    @api.constrains('name')
    def _check_name(self):
        for product in self:
            if self.product_name_is_already_existing(product.name):
                msg = _(f"Service Product named {product.name} is already exist!")
                raise ValidationError(msg)


class ProductProduct(models.Model):
    _inherit = 'product.product'

    is_delivery = fields.Boolean(related='product_tmpl_id.is_delivery', string="Is Delivery")
    is_special_discount = fields.Boolean(related='product_tmpl_id.is_special_discount', string="Is Special")
    is_down_payment = fields.Boolean(related='product_tmpl_id.is_down_payment', string="Is Down Payment")
