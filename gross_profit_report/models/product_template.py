from odoo import models, fields, api, tools

class ProductTemplate(models.Model): 
	_inherit = 'product.template'

	# to get faster query
	last_purchase_multi_uom_id = fields.Integer(default = False, compute='_compute_last_purchase_line', store = True)
	last_purchase_price_unit = fields.Float(default = 0.0, compute='_compute_last_purchase_line', store = True)


	def _compute_last_purchase_line(self):
		for rec in self:

			product_id = self.env['product.product'].search([('product_tmpl_id', '=', rec.id)])

			last_purchase_line = self.env['purchase.order.line'].search([
													('product_id', '=', product_id.id), 
													('state', 'in', ['done', 'purchase']),
													('price_unit', '>', 0)
												], order = 'date_planned desc', limit = 1) or False
			if last_purchase_line:
				rec.last_purchase_multi_uom_id, rec.last_purchase_price_unit = last_purchase_line.multi_uom_line_id, last_purchase_line.price_unit