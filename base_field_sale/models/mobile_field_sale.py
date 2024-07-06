from odoo import api, models, fields, _
from odoo.exceptions import UserError


class MobileDevice(models.Model):

    _name = 'mobile.device'
    _description = 'Mobile Device'
    _order = 'active desc'

    name = fields.Char('Name')
    active = fields.Boolean('Active Status', default=True)
    device_model = fields.Char('Model')
    device_imei = fields.Char('IMEI Code', copy=False)
    register_date = fields.Date('Registered Date', default=lambda self: fields.Date.context_today(self))
    sale_team_id = fields.Many2one('crm.team', 'Sale Team', domain=[('is_van_team', '=', True)])
    registered_by_user_id = fields.Many2one('res.users', 'Registered By')
    expire_date = fields.Date('Expire Date')
    is_admin = fields.Boolean('Is Admin', compute='_compute_is_admin')
    reject_reason = fields.Text('Reject Reason')
    state = fields.Selection([('draft', 'Waiting'),
                              ('approve', 'Approved'),
                              ('reject', 'Rejected')], 'State', default='draft')
    company_id = fields.Many2one('res.company', string='Company')

    _sql_constraints = [
        ('unique_device_imei', 'unique(device_imei)', "Device IMEI has to be unique!"),
    ]

    def _compute_is_admin(self):
        for rec in self:
            if self.env.is_admin():
                rec.is_admin = True
            else:
                rec.is_admin = False

    def btn_approve(self):
        for rec in self:
            if rec.state != 'draft':
                raise UserError('Some of the records you have selected are already approved or rejected.')
            rec.write({'state': 'approve'})

    def btn_reject(self):
        if any([rec.state != 'draft' for rec in self]):
            raise UserError('Some of the records you have selected are already approved or rejected.')
        context = dict(self.env.context)
        context['default_device_ids'] = [(6, 0, self.ids)]
        return {
            'name': 'Reject Reason',
            'type': 'ir.actions.act_window',
            'res_model': 'mobile.device.reject.reason',
            'view_mode': 'form',
            'target': 'new',
            'context': context,
        }
