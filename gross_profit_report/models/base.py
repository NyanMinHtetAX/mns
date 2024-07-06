
import odoo
from odoo import api, http, models

class Base(models.AbstractModel):
	_inherit = 'base'
	
	def _current_user_for_gp_report(self):
		current_user = self.env['res.users'].browse([self._context.get('uid', False)])

		user_db = self.env['gross_profit_report.db']
		if current_user:
			user_db.search([]).sudo().unlink()
			user_db.sudo().create({
				'uuid': current_user.id,
				'allowed_company_ids': ','.join(map(str, current_user.company_ids.ids))
			})

	@api.model
	def fields_view_get(self, view_id=None, view_type='form', toolbar=False, submenu=False):
		r = super().fields_view_get(view_id, view_type, toolbar, submenu)
		self._current_user_for_gp_report()

		if r.get('model', False) in ['sale.order', 'gross_profit_report.gross_profit_sql_report']:
			self.env['gross_profit_report.gross_profit_sql_report'].init()
		return r