from odoo import api, models, fields


class ProductPackaging(models.Model):
    _inherit = 'product.packaging'

    multi_uom_id = fields.Many2one('multi.uom.line', string = 'Multi UOM')
    avaiable_multi_uoms = fields.Many2many('multi.uom.line', compute = '_compute_from_product_multi_uoms')
    use_in_pos = fields.Boolean(default = True, string = 'Point of Sale')
    name = fields.Char(related = 'multi_uom_id.uom_id.name')

    @api.depends('product_id')
    def _compute_from_product_multi_uoms(self):
        for rec in self:
            rec.avaiable_multi_uoms = rec.product_id.multi_uom_line_ids.ids