from odoo import api, models, fields, _
from odoo.addons.sale_purchase_inter_company_rules.models.sale_order import sale_order as OriginalSaleOrder

from odoo import api, fields, models, exceptions, _
from odoo import SUPERUSER_ID
from odoo.exceptions import UserError


class SaleOrder(models.Model):
    _inherit = "sale.order"

    @api.model
    def _prepare_purchase_order_line_data(self, so_line, date_order, company):
        """ Generate purchase order line values, from the SO line
            :param so_line : origin SO line
            :rtype so_line : sale.order.line record
            :param date_order : the date of the orgin SO
            :param company : the company in which the PO line will be created
            :rtype company : res.company record
        """
        # price on PO so_line should be so_line - discount
        price = so_line.price_unit - (so_line.price_unit * (so_line.discount / 100))
        quantity = so_line.product_id and so_line.product_uom._compute_quantity(so_line.product_uom_qty, so_line.product_id.uom_po_id) or so_line.product_uom_qty
        price = so_line.product_id and so_line.product_uom._compute_price(price, so_line.product_id.uom_po_id) or price

        return {
            'name': so_line.name,
            'product_qty': quantity,
            'purchase_uom_qty': quantity / so_line.multi_uom_line_id.ratio,
            'multi_uom_line_id': so_line.multi_uom_line_id.id,
            'product_id': so_line.product_id and so_line.product_id.id or False,
            'product_uom': so_line.product_id and so_line.product_id.uom_po_id.id or so_line.product_uom.id,
            'price_unit': price or 0.0,
            'company_id': company.id,
            'date_planned': so_line.order_id.expected_date or date_order,
            'display_type': so_line.display_type,
        }

    OriginalSaleOrder._prepare_purchase_order_line_data = _prepare_purchase_order_line_data


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    product_uom_qty = fields.Float(compute='compute_product_uom_qty',
                                   inverse='set_multi_uom_qty',
                                   store=True,
                                   readonly=False)
    qty_delivered_manual = fields.Float(compute='compute_manual_delivered_qty',
                                        inverse='set_multi_qty_delivered_manual',
                                        store=True)
    multi_uom_line_id = fields.Many2one('multi.uom.line', 'UoM')
    uom_ratio_remark = fields.Char(string='Ratio Remark', related='multi_uom_line_id.remark')
    multi_uom_qty = fields.Float('UOM Qty',
                                 digits='Product Unit of Measure',
                                 default=1.0)
    multi_qty_delivered = fields.Float('DeliveredQuantity',
                                       copy=False,
                                       compute='_compute_multi_qty_delivered',
                                       inverse='_inverse_multi_qty_delivered',
                                       store=True,
                                       digits='Product Unit of Measure',
                                       default=0.0)
    multi_qty_delivered_manual = fields.Float('DeliveredManually',
                                              copy=False,
                                              digits='Product Unit of Measure',
                                              default=0.0)
    multi_qty_to_invoice = fields.Float(compute='_get_to_multi_invoice_qty',
                                        string='Invoice Qty',
                                        store=True,
                                        digits='Product Unit of Measure')
    multi_qty_invoiced = fields.Float(compute='_compute_multi_qty_invoiced',
                                      string='Invoiced Qty',
                                      store=True,
                                      digits='Product Unit of Measure')
    price_unit = fields.Float(compute='compute_multi_price_unit',
                              inverse='set_multi_price_unit',
                              store=True,
                              digits='Multi Product Price')
    multi_price_unit = fields.Float('Multi Price Unit', digits='Product Price', copy=False)
    multi_uom_discount = fields.Float('Discount')
    multi_uom_line_ids = fields.Many2many('multi.uom.line', compute='compute_multi_uom_line_ids')
    discount_amt = fields.Float(compute='_compute_multi_uom_discount',
                                inverse='_set_multi_uom_discount',
                                store=True,
                                digits='Multi UoM Discount')

    @api.depends('multi_uom_line_id', 'multi_uom_discount', 'discount_type')
    def _compute_multi_uom_discount(self):
        for line in self:
            if line.multi_uom_line_id and line.discount_type == 'fixed':
                line.discount_amt = line.multi_uom_discount / line.multi_uom_line_id.ratio
            else:
                line.discount_amt = line.multi_uom_discount

    def _set_multi_uom_discount(self):
        for line in self:
            if line.multi_uom_line_id:
                line.multi_uom_discount = line.discount_amt * line.multi_uom_line_id.ratio
            else:
                line.multi_uom_discount = line.discount_amt

    @api.depends('product_id')
    def compute_multi_uom_line_ids(self):
        for rec in self:
            rec.multi_uom_line_ids = rec.product_id.multi_uom_line_ids.ids

    @api.onchange('product_uom', 'product_uom_qty')
    def product_uom_change(self):
        res = super(SaleOrderLine, self).product_uom_change()
        if self.multi_price_unit:
            self.compute_multi_price_unit()
        return res

    @api.onchange('product_id')
    def product_id_change(self):
        res = super(SaleOrderLine, self).product_id_change()
        line = self.product_id.multi_uom_line_ids.filtered(lambda l: l.is_default_uom == True)
        self.multi_uom_line_id = line.id
        return res

    @api.onchange('product_uom', 'product_uom_qty', 'multi_uom_line_id')
    def product_uom_change(self):
        res = super().product_uom_change()
        return res

    def _get_display_price(self, product):
        pricelist_mode = self.env['ir.config_parameter'].get_param('product.product_pricelist_setting')
        if self.multi_uom_line_id and pricelist_mode == 'uom':
            if product.detailed_type != 'service':
                uom_price = self.order_id.pricelist_id._get_pricelist_uom_price(self.product_id, self.multi_uom_line_id,
                                                                                self.multi_uom_qty)
                self.multi_price_unit = uom_price

                price = uom_price / self.multi_uom_line_id.ratio
            else:
                price = product.list_price
        elif self.multi_uom_line_id and pricelist_mode =="advanced":
            if product.detailed_type != 'service':
                uom_price = self.order_id.pricelist_id._get_pricelist_uom_price(self.product_id, self.multi_uom_line_id,
                                                                                self.multi_uom_qty)
                
                self.multi_price_unit = uom_price

                price = uom_price / self.multi_uom_line_id.ratio
            else:
                price = product.list_price
        else:
            price = super(SaleOrderLine, self)._get_display_price(product)
            if self.multi_uom_line_id:
                self.multi_price_unit = price * self.multi_uom_line_id.ratio
        return price

    @api.depends('multi_uom_line_id', 'multi_uom_qty')
    def compute_product_uom_qty(self):
        for rec in self:
            if rec.multi_uom_line_id:
                rec.product_uom_qty = rec.multi_uom_qty * rec.multi_uom_line_id.ratio
            else:
                rec.product_uom_qty = 0

    def set_multi_uom_qty(self):
        for rec in self:
            if rec.multi_uom_line_id:
                rec.multi_uom_qty = rec.product_uom_qty / rec.multi_uom_line_id.ratio

    @api.depends('multi_uom_line_id', 'qty_invoiced')
    def _compute_multi_qty_invoiced(self):
        for rec in self:
            if rec.multi_uom_line_id:
                rec.multi_qty_invoiced = rec.qty_invoiced / rec.multi_uom_line_id.ratio
            else:
                rec.multi_qty_invoiced = 0

    @api.depends('multi_uom_line_id', 'qty_to_invoice')
    def _get_to_multi_invoice_qty(self):
        for rec in self:
            if rec.multi_uom_line_id:
                rec.multi_qty_to_invoice = rec.qty_to_invoice / rec.multi_uom_line_id.ratio
            else:
                rec.multi_qty_to_invoice = 0

    @api.depends('multi_uom_line_id', 'qty_delivered')
    def _compute_multi_qty_delivered(self):
        
        for rec in self:
            if rec.multi_uom_line_id:
                rec.multi_qty_delivered = rec.qty_delivered / rec.multi_uom_line_id.ratio
            else:
                rec.multi_qty_delivered = 0

    @api.depends('multi_uom_line_id', 'multi_qty_delivered')
    def _inverse_multi_qty_delivered(self):
        for rec in self:
            rec.qty_delivered = rec.multi_qty_delivered * rec.multi_uom_line_id.ratio

    @api.depends('multi_uom_line_id', 'multi_qty_delivered_manual')
    def compute_manual_delivered_qty(self):
        for rec in self:
            rec.qty_delivered_manual = rec.multi_qty_delivered_manual * rec.multi_uom_line_id.ratio

    def set_multi_qty_delivered_manual(self):
        for rec in self:
            rec.multi_qty_delivered_manual = rec.qty_delivered_manual * rec.multi_uom_line_id.ratio

    @api.depends('multi_uom_line_id', 'multi_price_unit')
    def compute_multi_price_unit(self):
        for rec in self:
            if rec.multi_uom_line_id:
                rec.price_unit = rec.multi_price_unit / rec.multi_uom_line_id.ratio
            else:
                rec.price_unit = rec.multi_price_unit

    def set_multi_price_unit(self):
        for rec in self:
            if rec.order_id.sale_type == 'normal':
                if rec.multi_uom_line_id:
                    rec.multi_price_unit = rec.price_unit * rec.multi_uom_line_id.ratio
                else:
                    rec.multi_price_unit = rec.price_unit
            else:
                rec.multi_price_unit = rec.multi_price_unit

    def _prepare_procurement_values(self, group_id=False):
        values = super(SaleOrderLine, self)._prepare_procurement_values(group_id)
        values.update({
            'multi_uom_line_id': self.multi_uom_line_id.id,
        })
        return values

    def _prepare_invoice_line(self, **optional_values):
        values = super(SaleOrderLine, self)._prepare_invoice_line(**optional_values)
        values['multi_uom_discount'] = self.multi_uom_discount
        values['multi_uom_line_id'] = self.multi_uom_line_id.id
        return values
