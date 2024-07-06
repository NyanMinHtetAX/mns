from odoo import api, fields, models, tools, _


class VisitReportImage(models.Model):
    _name = 'visit.report.image'
    _description = 'Visit Report Image'

    name = fields.Char('Name')
    image = fields.Binary('Image', attachment=True)
    image_id = fields.Many2one('visit.report', string='Report Visit Image')
