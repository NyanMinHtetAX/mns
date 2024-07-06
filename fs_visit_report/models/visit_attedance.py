from odoo import api, models, fields


class FsVisitAttendance(models.Model):

    _name = 'fs.visit.attendance'
    _description = 'FS Visit Attendance'
    _rec_name = 'team_id'

    partner_id = fields.Many2one('res.partner', 'Customer')
    team_id = fields.Many2one('crm.team', 'Sales Team')
    user_id = fields.Many2one('res.users', 'Salesperson')
    check_in = fields.Datetime('Check In')
    check_out = fields.Datetime('Check Out')
    duration = fields.Char('Duration')
    company_id = fields.Many2one('res.company', 'Company', default=lambda self: self.env.company.id)
