from odoo import api, models, fields, _


class VisitReport(models.Model):

    _name = 'visit.report'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Visit Report'

    name = fields.Char('Name')
    partner_id = fields.Many2one('res.partner','Customer')
    sale_team = fields.Many2one('crm.team','Sale Team', domain=[('is_van_team', '=', True)])
    sale_man = fields.Many2one('res.users','Sales Man')
    reason = fields.Char('Reason')
    date = fields.Date('Date', default=fields.Date.context_today)
    vehicles = fields.Many2one('fleet.vehicle','Vehicles')
    latitude = fields.Float("Lat",digits=(24, 12))
    longitude = fields.Float("Long",digits=(24, 12))
    other_reason = fields.Char('Other Reason')
    image_ids = fields.One2many('visit.report.image', 'image_id', string='Images')
    reason_type_id = fields.Many2one('visit.report.reason.type', 'Reason Type')
    company_id = fields.Many2one('res.company', 'Company', default=lambda self: self.env.company.id, required=1)

    # images = fields.Many2many(
    #     'ir.attachment', string='Images')
    map_widget = fields.Char('Map Widget')
    note = fields.Text("Notes")

    def add_images(self):
        return {
            'name' : 'Add Image',
            'type' : 'ir.actions.act_window',
            'target' : 'new',
            'view_mode' : 'form',
            'res_model' : 'visit.report.image'
        }

    def btn_show_map(self):
        ctx = self.env.context.copy()
        ctx.update({
            'default_latitude': self.latitude,
            'default_longitude': self.longitude,
        })
        return {
            'name': 'Visit Report Map',
            'type': 'ir.actions.act_window',
            'res_model': 'visit.report.map',
            'view_mode': 'form',
            'context': ctx,
        }


class VisitReportReasonType(models.Model):

    _name = 'visit.report.reason.type'
    _description = 'Visit Report Reason Type'

    name = fields.Char('Reason Type', required=True)
    description = fields.Text('Description')
