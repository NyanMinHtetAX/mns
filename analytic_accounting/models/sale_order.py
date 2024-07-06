from odoo import api, models, fields


class SaleOrder(models.Model):

    _inherit = 'sale.order'

    analytic_account_id = fields.Many2one('account.analytic.account', 'Analytic Account')
    client_order_reference = fields.Char(string="Clinet Order Reference", copy=False, readonly=1)

    def action_confirm(self):
        res = super(SaleOrder, self).action_confirm()
        for picking in self.picking_ids:
            if self.team_id.is_van_team:
                picking.write({
                    'analytic_account_id': picking.sale_id.analytic_account_id.id,
                    'vehicle_no': str(
                        self.team_id.vehicle_id.model_id.brand_id.name + "/" + self.team_id.vehicle_id.model_id.name + "/" + self.team_id.vehicle_id.license_plate),
                })
        return res

    def _prepare_invoice(self):
        values = super(SaleOrder, self)._prepare_invoice()
        values['analytic_account_id'] = self.analytic_account_id.id
        return values

class SaleAdvancePaymentInv(models.TransientModel):
    _inherit = "sale.advance.payment.inv"

    def _prepare_invoice_values(self, order, name, amount, so_line):
        res = super()._prepare_invoice_values(order, name, amount, so_line)
        res['analytic_account_id'] = order.analytic_account_id.id
        return res
