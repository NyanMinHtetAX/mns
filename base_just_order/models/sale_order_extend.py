from odoo import models, fields, api, _


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    is_from_mobile_order = fields.Boolean(string='From Mobile Order?', default=False)

    def action_confirm(self):
        res = super(SaleOrder, self).action_confirm()
        for do_pick in self.picking_ids:
            do_pick.write({
                'is_from_mobile_order': self.is_from_mobile_order,

            })
        return res

    def _prepare_invoice(self):
        res = super(SaleOrder, self)._prepare_invoice()
        res.update({
            'is_from_mobile_order': self.is_from_mobile_order,
        })
        return res


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    is_from_mobile_order = fields.Boolean(string='From Mobile Order?', default=False)


class AccountMove(models.Model):
    _inherit = 'account.move'

    is_from_mobile_order = fields.Boolean(string='From Mobile Order?', default=False)








