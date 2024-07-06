from odoo import models, fields, api, _


class ResPartner(models.Model):
    _inherit = 'res.partner'

    is_driver = fields.Boolean(string="Is a driver")


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    driver_id = fields.Many2one('res.partner', string="Driver", domain=[('is_driver', '=', True)])

    @api.onchange('fleet_id')
    def onchange_driver(self):
        if self.fleet_id:
            self.driver_id = self.fleet_id.driver_id



