from odoo import models, fields


class AccountMove(models.Model):

    _inherit = 'account.move'

    sale_stock_return_id = fields.Many2one('sale.stock.return','Sale Return')


class AccountMoveLine(models.Model):

    _inherit = 'account.move.line'

    sale_stock_return_line_id = fields.Many2one('sale.stock.return.line','Sale Return Line')
