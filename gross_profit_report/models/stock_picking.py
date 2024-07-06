from odoo import models

class StockPicking(models.Model):
	_inherit = "stock.picking"

	def button_validate(self):
		res = super(StockPicking, self).button_validate()

		for picking in self:
			for move in picking.move_ids_without_package:
				if move.purchase_line_id:
					purchase_line = move.purchase_line_id
					if purchase_line.product_id and purchase_line.price_unit > 0:

						query = """UPDATE product_template SET last_purchase_price_unit=""" + str(
						purchase_line.price_unit) + """, last_purchase_multi_uom_id=""" + str(purchase_line.multi_uom_line_id.id) + """ WHERE id=""" + str(purchase_line.product_id.product_tmpl_id.id) + """;"""
						self.env.cr.execute(query)

		return res