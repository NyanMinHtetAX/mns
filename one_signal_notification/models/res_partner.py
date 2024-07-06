import logging
import requests
from odoo import models, fields, SUPERUSER_ID
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class Partner(models.Model):

    _inherit = 'res.partner'

    notification_token_ids = fields.One2many('onesignal.token', 'partner_id', 'Notification Tokens')

    def send_onesignal_notification(self, title, message, data_payload={}):
        app_id = self.env.company.onesignal_app_id
        if not app_id:
            raise UserError('Onesignal App ID is missing. Please configure it in general settings.')
        player_ids = self.notification_token_ids
        player_ids = [player_id.token for player_id in player_ids if player_id.token]
        payload = {
            'app_id': app_id,
            'include_android_reg_ids': player_ids,
            'headings': {'en': title},
            'contents': {'en': message},
            'data': data_payload,
        }
        response = requests.post("https://onesignal.com/api/v1/notifications", json=payload, timeout=10)
        _logger.info(f'\nGot response from One Signal with status code of {response.status_code} and reason with'
                     f'{response.reason}.\n')


class OnesignalToken(models.Model):

    _name = 'onesignal.token'
    _description = 'Onesignal Token'
    _rec_name = 'token'

    token = fields.Char('Token', required=True)
    device = fields.Char('Device', required=True)
    partner_id = fields.Many2one('res.partner', 'Partner', ondelete='cascade')
