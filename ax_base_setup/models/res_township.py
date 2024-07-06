from odoo import api, fields, models


class ResTownship(models.Model):

    _name = "res.township"
    _description = 'Township'

    name = fields.Char(string='Township', required=True)
    code = fields.Char('Township Code')
    zip = fields.Char(string="Zip Code")
    city_id = fields.Many2one('res.city', string='City')
    city_code = fields.Char(string='City Code')
    state_id = fields.Many2one('res.country.state', string='State')
    country_id = fields.Many2one('res.country', string='Country')

    @api.onchange('city_id')
    def onchange_city(self):
        self.city_code = self.city_id.code
        self.state_id = self.city_id.state_id
        self.country_id = self.city_id.country_id
