from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    avail_in_mobile = fields.Boolean(string='Available in mobile', compute='')
    category_id = fields.Many2one('jr.category', string='Category', store=True)

    is_publish = fields.Boolean(string='Is Published', default=False)
    is_continue_selling = fields.Boolean(string='Out Of Stock', default=False)
    show_available_qty = fields.Boolean('Show Available Qty', default=False)

    available_onhand_limit = fields.Float(string='Onhand Limit', default=10.0)

    alternative_product_mcom_ids = fields.Many2many(
        'product.product', 'product_alternative_mcom_rel', 'tmpl_id', 'product_id', check_company=True,
        string='Alternative Products', help='Suggest alternatives to your customer (upsell strategy). '
                                            'Those products show up on the product page.')

    sale_description = fields.Text(string='Description')

    product_mcom_image_ids = fields.One2many('product.jr.images', 'product_tmpl_mcom_id', string="Extra Product Media",
                                             limit=4,
                                             copy=True)

    @api.constrains('product_mcom_image_ids')
    def set_limit_image(self):
        image_data = []
        if self.product_mcom_image_ids:
            for rec in self.product_mcom_image_ids:
                image_data.append(rec.id)
        if len(image_data) > 4:
            raise ValidationError(_("Maximum Product Images should be 4"))

    @api.depends('alternative_product_mcom_ids')
    def get_ava_data(self):
        if self.alternative_product_mcom_ids:
            for rec in self.alternative_product_mcom_ids:
                if not rec.avail_in_mobile:
                    rec.avail_in_mobile = True
                else:
                    pass

    @api.model
    def create(self, vals):

        res = super(ProductTemplate, self).create(vals)
        res.get_ava_data()
        return res

    def write(self, vals):
        res = super(ProductTemplate, self).write(vals)
        self.set_limit_image()
        self.get_ava_data()
        return res


# class ProductImage(models.Model):
#     _inherit = 'product.image'
#
#     product_tmpl_mcom_id = fields.Many2one('product.template', string='Images')


