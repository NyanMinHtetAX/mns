from odoo import api, models, fields


class NotifyWizard(models.TransientModel):

    _name = 'notify.wizard'
    _description = 'Notify Wizard'

    title = fields.Char('Title', required=1)
    message = fields.Text('Body', required=1)
    team_id = fields.Many2one('crm.team', required=1)

    def btn_notify(self):
        devices = self.env['mobile.device'].search([('sale_team_id', '=', self.team_id.id)])
        data_payload = {
            'id': self.env.context.get('active_id'),
            'model': self.env.context.get('active_model'),
        }
        devices.send_onesignal_notification(self.title, self.message, data_payload)
        if self.env.context.get('write_log'):
            record = self.env[self.env.context.get('active_model')].browse(self.env.context.get('active_id'))
            record.message_post(body=f'Notified to sale team({self.team_id.code}).')
