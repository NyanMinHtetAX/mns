from odoo import api, models, fields, _


class MobileDeviceRejectReason(models.TransientModel):

    _name = 'mobile.device.reject.reason'
    _description = 'Mobile Device Reject Reason'
    _rec_name = 'reason'

    reason = fields.Text('Reason')
    device_ids = fields.Many2many('mobile.device', 'device_reject_reason_rel', 'reason_id', 'device_id', 'Devices')

    def btn_reject(self):
        for device in self.device_ids:
            device.write({
                'reject_reason': self.reason,
                'state': 'reject',
            })
