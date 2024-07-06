from odoo import api, models, fields
from odoo.exceptions import ValidationError


class StockMove(models.Model):
    _inherit = 'stock.move'

    def _action_confirm(self, merge=True, merge_into=False):
        merge = merge_into = False
        return super(StockMove, self)._action_confirm(merge, merge_into)


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    def write(self, values):
        res = super(ProductTemplate, self).write(values)
        if self.uom_id:
            check_uom_lines = self.env['multi.uom.line'].search([('product_tmpl_id', '=', self.id)]).uom_id
            if self.uom_id not in check_uom_lines:
                raise ValidationError('Please Check in Multi UOM Line Tab')
        return res

