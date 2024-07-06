from odoo import models, fields, api, _


class ResPartnerOutlet(models.Model):
    _name = 'res.partner.outlet'
    _description = 'Outlet'

    name = fields.Char(string='Name')
    channel_id = fields.Many2one('res.sale.channel', string='Sale Channel')




