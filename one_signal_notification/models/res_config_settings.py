from odoo import api, models, fields


class Company(models.Model):

    _inherit = 'res.company'

    onesignal_app_id = fields.Char('Onesignal App ID')


class ResConfigSettings(models.TransientModel):

    _inherit = 'res.config.settings'

    onesignal_app_id = fields.Char('Onesignal App ID', related='company_id.onesignal_app_id', readonly=False)
