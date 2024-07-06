from odoo import api, models, fields


class Company(models.Model):

    _inherit = 'res.company'

    consignment_warehouse_id = fields.Many2one('stock.warehouse', 'Consignment Warehouse')


class ResConfigSettings(models.TransientModel):

    _inherit = 'res.config.settings'

    consignment_warehouse_id = fields.Many2one('stock.warehouse', 'Consignment Warehouse', 
                                               related='company_id.consignment_warehouse_id',
                                               readonly=False)
