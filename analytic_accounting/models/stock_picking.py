from odoo import api, models, fields


class StockPicking(models.Model):

    _inherit = 'stock.picking'

    analytic_account_id = fields.Many2one('account.analytic.account', 'Analytic Account')

    def _action_done(self):
        for picking in self:
            if picking.sale_id:
                picking.move_lines.write({'analytic_account_id': picking.sale_id.analytic_account_id.id})
            else:
                picking.move_lines.write({'analytic_account_id': picking.analytic_account_id.id})
        res = super(StockPicking, self)._action_done()
        return res
