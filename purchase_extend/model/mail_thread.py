from odoo import models, fields

class MailThread(models.AbstractModel):
	_inherit = 'mail.thread'

	def _message_auto_subscribe_followers(self, updated_values, default_subtype_ids):
		return []