from odoo import api, models, fields


class StockMove(models.Model):

    _inherit = 'stock.move'

    consignment_line_id = fields.Many2one('consignment.line', 'Consignment Line')
    consignment_requisition_id = fields.Many2one('consignment.requisition', 'Consignment Requisition')

