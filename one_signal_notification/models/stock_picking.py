from odoo import api, models, fields
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from odoo.exceptions import UserError
from datetime import datetime


class StockPicking(models.Model):

    _inherit = 'stock.picking'

    def button_validate(self):
        res = super(StockPicking, self).button_validate()
        requests = self.filtered(lambda p: p.is_requisition and p.state == 'assigned')
        for request in requests:
            devices = self.env['mobile.device'].search([('sale_team_id', '=', request.team_id.id)])
            title = 'Stock Request Approved'
            message = f'Your stock request({request.name}) has been approved.'
            data_payload = {
                'id': request.id,
                'name': request.name,
                'model': request._name,
                'state': request.state,
            }
            actions = {
                "buttons": [
                    {
                        "action": "like-button",
                        "title": "Like",
                        "icon": "http://i.imgur.com/N8SN8ZS.png",
                        "url": "https://example.com"
                    },
                    {
                        "action": "read-more-button",
                        "title": "Read more",
                        "icon": "http://i.imgur.com/MIxJp1L.png",
                        "url": "https://example.com"
                    }
                ],
                "action": "like-button"
            }
            devices.send_onesignal_notification(title, message, data_payload)
        return res
