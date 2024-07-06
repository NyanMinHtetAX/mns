from odoo import models, fields, api, _


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    def action_confirm(self):
        res = super(SaleOrder, self).action_confirm()
        if self.order_line:
            for line in self.order_line:
                values = {
                    'partner_id': self.partner_id.id,
                    'ticket_number': self.name,
                    'ticket_date': self.date_order,
                    'currency_id': self.currency_id.id,
                    'product_tmpl_id': line.product_id.id,
                    'price': line.price_unit,
                    'sale_qty': line.product_uom_qty,
                }
                self.env['sale.pricelist.record'].create(values)
                if line.product_id:
                    product_template_id = self.env['product.template'].search(
                        [('id', '=', line.product_id.product_tmpl_id.id)])
                    if product_template_id:
                        product_template_id.write({
                            'final_sale_price': line.multi_price_unit
                        })

        return res


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    def action_sale_price_list_info(self):
        records = self.env['sale.pricelist.record'].search([('product_tmpl_id.name', '=', self.product_id.name)],
                                                           order='ticket_date desc', limit=5)
        info_line = {
            'name': 'Last Sale PriceList History',
            'type': 'ir.actions.act_window',
            'res_model': 'sale.pricelist.record',
            'target': 'new',
            'context': {'tree_view_ref': 'sale_pricelist_record_tree_view'},
            'domain': [('id', 'in', records.ids)],
            'view_mode': 'tree',
        }
        return info_line
