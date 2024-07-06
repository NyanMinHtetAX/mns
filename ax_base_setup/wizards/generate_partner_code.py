from odoo import api, models


class GeneratePartnerCode(models.TransientModel):

    _name = 'generate.partner.code'
    _description = 'Generate Partner Code'

    def action_generate_sequence(self):
        active_ids = self._context.get('active_ids', [])
        partner_ids = self.env['res.partner'].browse(active_ids)
        partner_ids.generate_sequence_code()
        partner_ids.customer = True
