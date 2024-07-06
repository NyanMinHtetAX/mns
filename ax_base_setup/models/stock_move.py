from odoo import api, models, fields


class StockMove(models.Model):

    _inherit = 'stock.move'

    is_foc = fields.Boolean('FOC', related='sale_line_id.is_foc', store=True)


class StockMoveLine(models.Model):

    _inherit = 'stock.move.line'

    is_foc = fields.Boolean('FOC', related='move_id.is_foc', store=True)
