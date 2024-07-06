from odoo import models, fields, api, _


class DeliveryAppDevice(models.Model):

    _name = 'delivery.app.device'
    _description = 'Delivery App Device'
    _rec_name = 'device_id'

    active = fields.Boolean('Active Status', default=True)
    delivery_man_id = fields.Many2one('res.users', 'Delivery Man', required=1, domain=[('is_delivery_man', '=', True),
                                                                                       ('is_portal_user', '=', True)])
    device_model = fields.Char('Device Model', required=1)
    device_id = fields.Char('Device ID', required=1)
    fcm_token = fields.Char(string='FCM Token', required=1)
