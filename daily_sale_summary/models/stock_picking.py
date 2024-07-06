from odoo import models, fields


class StockPicking(models.Model):

    _inherit = 'stock.picking'

    van_order_id = fields.Many2one('van.order', 'Van Order')
    daily_sale_summary_id = fields.Many2one('daily.sale.summary', 'Daily Sale Summary',
                                            related='van_order_id.daily_sale_summary_id', store=True)
