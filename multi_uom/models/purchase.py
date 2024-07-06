from odoo import api, fields, models, _
from odoo.addons.sale_purchase_inter_company_rules.models.purchase_order import purchase_order as OriginalPurchaseOrder


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    inter_company_transaction = fields.Boolean(string='Inter-Company Transaction', readonly=True)

    @api.model
    def _prepare_sale_order_line_data(self, line, company):
        """ Generate the Sales Order Line values from the PO line
            :param line : the origin Purchase Order Line
            :rtype line : purchase.order.line record
            :param company : the company of the created SO
            :rtype company : res.company record
        """
        # it may not affected because of parallel company relation
        price = line.price_unit or 0.0
        quantity = line.product_id and line.product_uom._compute_quantity(line.product_qty,
                                                                          line.product_id.uom_id) or line.product_qty
        price = line.product_id and line.product_uom._compute_price(price, line.product_id.uom_id) or price

        return {
            'name': line.name,
            'product_uom_qty': quantity,
            'multi_uom_qty': line.purchase_uom_qty,
            'multi_uom_line_id': line.multi_uom_line_id.id,
            'product_id': line.product_id and line.product_id.id or False,
            'product_uom': line.product_id and line.product_id.uom_id.id or line.product_uom.id,
            'price_unit': price,
            'multi_price_unit': line.multi_price_unit,
            'customer_lead': line.product_id and line.product_id.sale_delay or 0.0,
            'company_id': company.id,
            'display_type': line.display_type,
        }

    OriginalPurchaseOrder._prepare_sale_order_line_data = _prepare_sale_order_line_data

    def _add_supplier_to_product(self):
        for line in self.order_line:
            # Do not add a contact as a supplier
            partner = self.partner_id if not self.partner_id.parent_id else self.partner_id.parent_id
            if line.product_id and partner not in line.product_id.seller_ids.mapped('name') and len(
                    line.product_id.seller_ids) <= 10:
                # Convert the price in the right currency.
                currency = partner.property_purchase_currency_id or self.env.company.currency_id
                price = self.currency_id._convert(line.multi_price_unit, currency, line.company_id,
                                                  line.date_order or fields.Date.today(), round=False)
                # Compute the price for the template's UoM, because the supplier's UoM is related to that UoM.
                if line.product_id.product_tmpl_id.uom_po_id != line.product_uom:
                    default_uom = line.product_id.product_tmpl_id.uom_po_id
                    price = line.product_uom._compute_price(price, default_uom)

                supplierinfo = self._prepare_supplier_info(partner, line, price, currency)
                # In case the order partner is a contact address, a new supplierinfo is created on
                # the parent company. In this case, we keep the product name and code.
                seller = line.product_id._select_seller(
                    partner_id=line.partner_id,
                    quantity=line.product_qty,
                    date=line.order_id.date_order and line.order_id.date_order.date(),
                    uom_id=line.product_uom)
                if seller:
                    supplierinfo['product_name'] = seller.product_name
                    supplierinfo['product_code'] = seller.product_code
                vals = {
                    'seller_ids': [(0, 0, supplierinfo)],
                }
                try:
                    line.product_id.write(vals)
                except AccessError:  # no write access rights -> just ignore
                    break


class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    product_qty = fields.Float(compute='compute_multi_uom_line_qty',
                               inverse='set_multi_uom_line_qty',
                               store=True, readonly=False)
    price_unit = fields.Float('Price Unit',
                              compute='compute_multi_price_unit',
                              inverse='set_multi_price_unit', store=True, digits='Multi Product Price')
    multi_price_unit = fields.Float('PriceUnit')
    multi_uom_discount = fields.Float('Discount')
    purchase_uom_qty = fields.Float('UOM Qty', digits='Product Unit of Measure', default=1.0)
    multi_uom_line_id = fields.Many2one('multi.uom.line', 'Multi UOM Line', compute=False)
    uom_ratio_remark = fields.Char(string='Ratio Remark', related='multi_uom_line_id.remark')
    multi_qty_received = fields.Float('Qty Received',
                                      digits='Product Unit of Measure',
                                      compute='_compute_multi_qty_received',
                                      store=True)
    multi_qty_invoiced = fields.Float('Qty Billed',
                                      digits='Product Unit of Measure',
                                      compute='_compute_multi_qty_invoiced',
                                      store=True)
    multi_uom_line_ids = fields.Many2many('multi.uom.line', compute='compute_multi_uom_line_ids')

    discount = fields.Float(compute='_compute_multi_uom_discount',
                            inverse='_set_multi_uom_discount',
                            store=True,
                            digits='Multi UoM Discount')
    inter_company_transaction = fields.Boolean(
        related='order_id.inter_company_transaction',
        string='Inter-Company Transaction',
        readonly=True,
    )

    @api.depends('multi_uom_line_id', 'multi_uom_discount', 'discount_type')
    def _compute_multi_uom_discount(self):
        for line in self:
            if line.multi_uom_line_id and line.discount_type == 'fixed':
                line.discount = line.multi_uom_discount / line.multi_uom_line_id.ratio
            else:
                line.discount = line.multi_uom_discount

    def _set_multi_uom_discount(self):
        for line in self:
            if line.multi_uom_line_id:
                line.multi_uom_discount = line.discount * line.multi_uom_line_id.ratio
            else:
                line.multi_uom_discount = line.discount

    @api.onchange('product_qty', 'product_uom')
    def _onchange_quantity(self):
        super(PurchaseOrderLine, self)._onchange_quantity()
        self.compute_multi_price_unit()

    @api.depends('multi_uom_line_id', 'multi_price_unit')
    def compute_multi_price_unit(self):
        for rec in self:
            if rec.multi_uom_line_id:
                rec.price_unit = rec.multi_price_unit / rec.multi_uom_line_id.ratio
            else:
                rec.price_unit = rec.multi_price_unit

    def set_multi_price_unit(self):
        for rec in self:
            rec.multi_price_unit = rec.price_unit * rec.multi_uom_line_id.ratio

    @api.depends('product_id')
    def compute_multi_uom_line_ids(self):
        for rec in self:
            rec.multi_uom_line_ids = rec.product_id.multi_uom_line_ids.ids

    @api.model
    def create(self, values):
        res = super(PurchaseOrderLine, self).create(values)
        if not res.multi_uom_line_id:
            res.onchange_product_id()
        return res

    @api.onchange('product_id')
    def onchange_product_id(self):
        res = super(PurchaseOrderLine, self).onchange_product_id()
        self.multi_uom_line_id = self.product_id.multi_uom_line_ids.filtered(lambda l: l.is_default_uom == True)
        return res

    @api.depends('product_id', 'multi_uom_line_id', 'purchase_uom_qty')
    def compute_multi_uom_line_qty(self):
        for rec in self:
            rec.product_qty = rec.multi_uom_line_id.ratio * rec.purchase_uom_qty

    def set_multi_uom_line_qty(self):
        for rec in self:
            if rec.multi_uom_line_id:
                rec.purchase_uom_qty = rec.product_qty / rec.multi_uom_line_id.ratio
            else:
                rec.purchase_uom_qty = rec.product_qty

    @api.depends('multi_uom_line_id', 'qty_received')
    def _compute_multi_qty_received(self):
        for rec in self:
            if rec.multi_uom_line_id:
                rec.multi_qty_received = rec.qty_received / rec.multi_uom_line_id.ratio
            else:
                rec.multi_qty_received = rec.qty_received

    @api.depends('multi_uom_line_id', 'qty_invoiced')
    def _compute_multi_qty_invoiced(self):
        for rec in self:
            if rec.multi_uom_line_id:
                rec.multi_qty_invoiced = rec.qty_invoiced / rec.multi_uom_line_id.ratio
            else:
                rec.multi_qty_invoiced = rec.qty_invoiced

    def _prepare_stock_move_vals(self, picking, price_unit, product_uom_qty, product_uom):
        values = super(PurchaseOrderLine, self)._prepare_stock_move_vals(picking, price_unit, product_uom_qty,
                                                                         product_uom)
        values['multi_uom_line_id'] = self.multi_uom_line_id.id
        return values

    def _prepare_account_move_line(self, move=False):
        values = super(PurchaseOrderLine, self)._prepare_account_move_line(move)
        values['multi_uom_discount'] = self.multi_uom_discount
        values['multi_uom_line_id'] = self.multi_uom_line_id.id
        return values

    def _suggest_quantity(self):
        res = super(PurchaseOrderLine, self)._suggest_quantity()
        seller_min_qty = self.product_id.seller_ids \
            .filtered(
            lambda r: r.name == self.order_id.partner_id and (not r.product_id or r.product_id == self.product_id)) \
            .sorted(key=lambda r: r.min_qty)
        if seller_min_qty:
            self.purchase_uom_qty = seller_min_qty[0].min_qty or 1.0
            self.product_uom = seller_min_qty[0].product_uom
        else:
            self.purchase_uom_qty = 1.0
        return res


    @api.model
    def _prepare_purchase_order_line_from_procurement(self, product_id, product_qty, product_uom, company_id, values,
                                                      po):
        res = super(PurchaseOrderLine, self)._prepare_purchase_order_line_from_procurement(product_id,
                                                                                           product_qty,
                                                                                           product_uom,
                                                                                           company_id,
                                                                                           values,
                                                                                           po)
        res['multi_uom_line_id'] = values.get('multi_uom_line_id')
        res['purchase_uom_qty'] = values.get('purchase_uom_qty')
        return res
