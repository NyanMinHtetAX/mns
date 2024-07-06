from odoo import models, fields, api, _
from odoo.exceptions import UserError


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    purchaser_id = fields.Many2one(
        'res.users',
        string="Purchaser",
        copy=True
    )
    purchaser_id_name = fields.Char(
        related = 'purchaser_id.name',
        copy=False,
        tracking = True
    )  # Adding Purchaser By AMM  # To disable auto mailing when user is changed

    city_id = fields.Many2one('res.city', string='Cities', related='partner_id.x_city_id', store=True)

    def unlink(self):
        for order in self:
            if order.picking_ids:
                raise UserError(_('You can not remove an order line once the purchase order is receipt.'))
        return super(SaleOrder, self).unlink()

    @api.onchange('partner_id')
    def change_purchaser(self):
        for rec in self:
            if rec.partner_id and rec.partner_id.purchaser_id:
                rec.purchaser_id = rec.partner_id.purchaser_id
            else:
                rec.purchaser_id = False


class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    @api.onchange('product_id')
    def onchange_product(self):
        print( '//////////////////////')
        vendor_id = self.env['product.supplierinfo'].search([('product_tmpl_id.id','=',self.product_id.product_tmpl_id.id)])

        for line in self:
            for i in vendor_id:
                print(line.order_id.partner_id.id,'//////////////////////')
                print(i.name.id, '//////////////////////')
                if i.name.id == line.order_id.partner_id.id:
                    print(i.product_uom.name, '//////////////////////')
                    line.multi_price_unit = i.price
