from odoo import api, models, fields


class VisitReportMap(models.TransientModel):

    _name = 'visit.report.map'
    _description = 'Visit Report Map View'

    latitude = fields.Float('Latitude')
    longitude = fields.Float('Longitude')
    map_widget = fields.Char('Map Widget')

    def name_get(self):
        records = []
        for record in self:
            records.append((record.id, f'{record.latitude}, {record.longitude}'))
        return records
