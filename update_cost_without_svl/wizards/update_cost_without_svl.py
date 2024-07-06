from odoo import api, models, fields


class UpdateCostWithoutSvl(models.TransientModel):

    _name = 'update.cost.without.svl'
    _description = 'Update Cost Without SVL'

    cost = fields.Float('Cost')

    def update_cost_without_svl(self):
        ctx = self.env.context
        active_id = ctx.get('active_id')
        active_model = ctx.get('active_model')
        if active_model == 'product.template':
            products = self.env['product.template'].browse(active_id).product_variant_ids
        elif active_model == 'product.product':
            products = self.env['product.product'].browse(active_id)
        else:
            products = self.env['product.product']
        products.with_context(disable_auto_svl=True).write({'standard_price': self.cost})
