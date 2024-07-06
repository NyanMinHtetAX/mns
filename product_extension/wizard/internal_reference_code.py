from odoo import api, models


class InternalReferenceCode(models.TransientModel):
    _name = 'internal.reference.code'
    _description = 'Internal Reference Code'

    def action_product_tmpl_code(self):
        active_ids = self._context.get('active_ids', [])
        product_ids = self.env['product.template'].browse(active_ids)
        product_ids.generate_default_code()

    def action_product_code(self):
        active_ids = self._context.get('active_ids', [])
        product_ids = self.env['product.product'].browse(active_ids)
        product_ids.generate_default_code()
