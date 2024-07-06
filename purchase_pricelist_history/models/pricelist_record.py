# -*- coding: utf-8 -*-

from odoo import models, fields, api
from datetime import datetime
from odoo.addons import decimal_precision as dp


class PricelistRecord(models.Model):
    _name = 'pricelist.record'
    _description = 'Purchase Order Record based on Pricelist'

    name = fields.Many2one(
        'res.partner', 'Vendor',
        domain=[('supplier', '=', True)], ondelete='cascade', required=True,
        help="Vendor of this product")
    sequence = fields.Integer(
        'Sequence', default=1, help="Assigns the priority to the list of product vendor.")
    price = fields.Float(
        'Price', default=0.0, digits='Product Price',
        required=True, help="The price to purchase a product")
    currency_id = fields.Many2one(
        'res.currency', 'Currency',
        default=lambda self: self.env.user.company_id.currency_id.id,
        required=True)
    product_tmpl_id = fields.Many2one(
        'product.product', 'Product',
        index=True, ondelete='cascade')
    # index=True, ondelete='cascade', oldname='product_id')
    ticket_date = fields.Datetime(string="Ticket Date")
    ticket_number = fields.Char(string="PO Number", required=True)
    purchase_qty = fields.Integer(string="Purchase Quantity")


class PurchaseOrder(models.Model):
    _inherit = "purchase.order"
    
    def button_confirm(self):
        product_supplierinfo = self.env['product.supplierinfo']
        for order in self:
            if order.state not in ['draft', 'sent']:
                continue
            order._add_supplier_to_product()
            # Deal with double validation process
            if order.company_id.po_double_validation == 'one_step' \
                    or (order.company_id.po_double_validation == 'two_step' \
                        and order.amount_total < self.env.user.company_id.currency_id._convert(
                        order.company_id.po_double_validation_amount, order.currency_id, order.company_id,
                        order.date_order or fields.Date.today())) \
                    or order.user_has_groups('purchase.group_purchase_manager'):
                order.button_approve()
            else:
                order.write({'state': 'to approve'})
            if order.partner_id not in order.message_partner_ids:
                order.message_subscribe([order.partner_id.id])
            for line in order.order_line:
                values = {
                    'name': order.partner_id.id,
                    'ticket_number': order.name,
                    'ticket_date': order.date_order,
                    'currency_id': order.currency_id.id,
                    'product_tmpl_id': line.product_id.id,
                    'price': line.price_unit,
                    'purchase_qty': line.product_qty,
                }
                self.env['pricelist.record'].create(values)
                if line.product_id:
                    if line.multi_price_unit != 0:
                        quee = """UPDATE product_template SET final_purchase_price=""" + str(
                            line.multi_price_unit) + """ WHERE id=""" + str(line.product_id.product_tmpl_id.id) + """;"""
                        self.env.cr.execute(quee)
                    pricelist_ids = self.env['product.pricelist.item'].sudo().search(
                        [('product_id', '=', line.product_id.id)])

                    price = False
                    total_pricing = 0.0
                    # price_unit = line.product_id.final_purchase_price
                    price_unit = line.multi_price_unit
                    for rec in pricelist_ids:
                        if rec.compute_price == "fixed":
                            rec.total_price = rec.fixed_price
                        else:
                            if rec.base == 'final_purchase_price':
                                if rec.profit_percent:
                                    price = round(price_unit, 2) + rec.price_surcharge + rec.adjust_amounts
                                    rec.total_price = round(price + (price * (rec.profit_percent / 100)))
                                    total_pricing = rec.total_price
                                else:
                                    rec.total_price = round(price_unit, 2) + rec.price_surcharge + rec.adjust_amounts
                                    total_pricing = rec.total_price

                for item in pricelist_ids:
                    if item.base != 'final_purchase_price':
                        if item.base_pricelist_id.item_ids:
                            default_uom_id = item.product_id.multi_uom_line_ids.filtered(
                                lambda l: l.is_default_uom == True)
                            if item.multi_uom_line_id == default_uom_id:
                                for rec in item.base_pricelist_id.item_ids:
                                    if item.product_id == rec.product_id:
                                        default_uom_id = item.product_id.multi_uom_line_ids.filtered(
                                            lambda l: l.is_default_uom == True)

                                        if item.profit_percent:
                                            price = total_pricing + item.price_surcharge + item.adjust_amounts
                                            item.total_price = round(price + (price * (item.profit_percent / 100)))
                                            break
                                        else:
                                            item.total_price = total_pricing + item.price_surcharge + item.adjust_amounts
                                            break
                                    else:
                                        item.total_price = 0.0
                                print(item.total_price, item.product_id.name, 'l....................')
                            else:
                                if item.min_quantity == 1:
                                    for rec in item.base_pricelist_id.item_ids:

                                        if item.product_id == rec.product_id:
                                            default_uom_id = item.product_id.multi_uom_line_ids.filtered(
                                                lambda l: l.is_default_uom == True)

                                            try:
                                                t_price = round(total_pricing * (
                                                            item.multi_uom_line_id.ratio / default_uom_id.ratio))
                                            except:
                                                pass
                                            if item.profit_percent:
                                                price = t_price + item.price_surcharge + item.adjust_amounts
                                                item.total_price = round(price + (price * (item.profit_percent / 100)))
                                                break
                                            else:
                                                item.total_price = (t_price + item.price_surcharge + item.adjust_amounts)
                                                break
                                        else:
                                            item.total_price = 0.0
                                else:

                                    for rec in item.base_pricelist_id.item_ids:
                                        if item.product_id == rec.product_id:
                                            default_uom_id = rec.product_id.multi_uom_line_ids.filtered(
                                                lambda l: l.is_default_uom == True)

                                            try:
                                                t_price = round(total_pricing * (
                                                            item.multi_uom_line_id.ratio / default_uom_id.ratio))
                                            except:
                                                pass

                                            if item.profit_percent:
                                                price = t_price + item.price_surcharge + item.adjust_amounts
                                                item.total_price = round(price + (price * (item.profit_percent / 100)))
                                                break
                                            else:
                                                item.total_price = (t_price + item.price_surcharge + item.adjust_amounts)

                                                break
                                        else:
                                            item.total_price = 0.0

                        else:
                            rec.total_price = 0.0
                pricelist_ids = self.env['product.pricelist.item'].sudo().search(
                    [('product_id', '=', line.product_id.id)])

                price = False
                # price_unit = line.product_id.final_purchase_price
                price_unit = line.multi_price_unit
                for rec in pricelist_ids:
                    if rec.compute_price == "fixed":
                        rec.total_price = rec.fixed_price
                    else:
                        if rec.base == 'final_purchase_price':
                            if rec.profit_percent:
                                price = price_unit + rec.price_surcharge + rec.adjust_amounts
                                rec.total_price = round(price + (price * (rec.profit_percent / 100)))
                            else:
                                rec.total_price = price_unit + rec.price_surcharge + rec.adjust_amounts

        return True


class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    def action_stock_replenishment_info(self):
        records = self.env['pricelist.record'].search([('product_tmpl_id.name', '=', self.product_id.name)],
                                                      order='ticket_date desc', limit=5)
        info_line = {
            'name': 'Final Purchase Pricelist History',
            'type': 'ir.actions.act_window',
            'res_model': 'pricelist.record',
            'target': 'new',
            'context': {'tree_view_ref': 'pricelist_record_tree_view'},
            'domain': [('id', 'in', records.ids)],
            'view_mode': 'tree',
        }
        return info_line


class ProductTemplate(models.Model):
    _inherit = "product.template"

    final_purchase_price = fields.Float("Final Purchase Price")
