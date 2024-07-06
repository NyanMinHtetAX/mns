import logging
import requests
from odoo import models, fields, SUPERUSER_ID
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class MobileDevice(models.Model):

    _inherit = 'mobile.device'

    notification_token = fields.Text('Notification Token')

    def send_onesignal_notification(self, title, message, data_payload={}, actions={}):
        app_id = self.env.company.fs_onesignal_app_id
        if not app_id:
            raise UserError('Onesignal App ID is missing. Please configure it in field sales settings.')
        tokens = [device.notification_token for device in self if device.notification_token]
        if not tokens:
            _logger.info(f'Token missing for devices {self.ids} : {self.mapped("name")}')
            return
        payload = {
            'app_id': app_id,
            'include_player_ids': tokens,
            # 'include_android_reg_ids': tokens,
            'headings': {'en': title},
            'contents': {'en': message},
            'data': data_payload,
        }
        payload.update(actions)
        response = requests.post("https://onesignal.com/api/v1/notifications", json=payload, timeout=10)
        _logger.info(f'\nGot response from One Signal with status code of {response.status_code} and reason with'
                     f'{response.reason}.\n')
