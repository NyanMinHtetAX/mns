from odoo import api, models, fields


class PosOrder(models.Model):

    _inherit = 'pos.order'

    def _prepare_invoice_line(self, order_line):
        values = super(PosOrder, self)._prepare_invoice_line(order_line)
        values['multi_uom_line_id'] = order_line.multi_uom_line_id.id
        return values


class PosOrderLine(models.Model):

    _inherit = 'pos.order.line'

    qty = fields.Float(compute='_compute_product_uom_qty',
                       inverse='_set_multi_uom_qty',
                       store=True,
                       digits='Product Unit of Measure')
    price_unit = fields.Float(compute='_compute_product_uom_price',
                              inverse='_set_multi_uom_price',
                              store=True,
                              digits='Multi Product Price')
    discount = fields.Float(compute='_compute_product_uom_discount',
                            inverse='_set_multi_uom_discount',
                            store=True,
                            digits='Multi UoM Discount')
    multi_uom_line_id = fields.Many2one('multi.uom.line', 'Multi UoM Line')
    multi_uom_line_ids = fields.Many2many('multi.uom.line',
                                          string='Multi UoM Lines',
                                          compute='_compute_multi_uom_line_ids')
    multi_uom_qty = fields.Float('Multi UoM Qty')
    multi_uom_price = fields.Float('Multi UoM Price Unit')
    multi_uom_discount = fields.Float('Multi UoM Discount')

    @api.model
    def create(self, vals):
        if 'multi_uom_line_id' not in vals:
            product = self.env['product.product'].browse(vals['product_id'])
            multi_uom_line_id = product.multi_uom_line_ids.filtered(lambda l: l.uom_id.id == product.uom_id.id)

            if len(multi_uom_line_id) > 1:
                multi_uom_line_id = multi_uom_line_id[0]

            vals['multi_uom_line_id'] = multi_uom_line_id.id
        return super(PosOrderLine, self).create(vals)

    def _compute_multi_uom_line_ids(self):
        for line in self:
            line.multi_uom_line_ids = line.product_id.multi_uom_line_ids

    @api.depends('multi_uom_line_id', 'multi_uom_qty')
    def _compute_product_uom_qty(self):
        for line in self:
            if line.multi_uom_line_id:
                line.qty = line.multi_uom_qty * line.multi_uom_line_id.ratio
            else:
                line.qty = line.multi_uom_qty

    @api.depends('multi_uom_line_id', 'qty')
    def _set_multi_uom_qty(self):
        for line in self:
            if line.multi_uom_line_id:
                line.multi_uom_qty = line.qty / line.multi_uom_line_id.ratio
            else:
                line.multi_uom_qty = line.qty

    @api.depends('multi_uom_line_id', 'multi_uom_price')
    def _compute_product_uom_price(self):
        for line in self:
            if line.multi_uom_line_id:
                line.price_unit = line.multi_uom_price / line.multi_uom_line_id.ratio
            else:
                line.price_unit = line.multi_uom_price

    @api.depends('multi_uom_line_id', 'price_unit')
    def _set_multi_uom_price(self):
        for line in self:
            if line.multi_uom_line_id:
                line.multi_uom_price = line.price_unit * line.multi_uom_line_id.ratio
            else:
                line.multi_uom_price = line.price_unit

    @api.depends('multi_uom_line_id', 'multi_uom_discount')
    def _compute_product_uom_discount(self):
        for line in self:
            if line.multi_uom_line_id:
                line.discount = line.multi_uom_discount / line.multi_uom_line_id.ratio
            else:
                line.discount = line.multi_uom_discount

    @api.depends('multi_uom_line_id', 'discount')
    def _set_multi_uom_discount(self):
        for line in self:
            if line.multi_uom_line_id:
                line.multi_uom_discount = line.discount * line.multi_uom_line_id.ratio
            else:
                line.multi_uom_discount = line.discount

    def _export_for_ui(self, orderline):
        values = super(PosOrderLine, self)._export_for_ui(orderline)
        values['multi_uom_line_id'] = orderline.multi_uom_line_id.id
        return values

    @api.model
    def _order_line_fields(self, line, session_id=None):

        order_line = super(PosOrderLine, self)._order_line_fields(line, session_id)

        values = order_line[2]

        qty = values['qty']
        discount = values['discount']
        price_unit = values['price_unit']
        product = self.env['product.product'].browse(values['product_id'])
        if not values.get('multi_uom_line_id'):
            multi_uom_line_id = product.multi_uom_line_ids.filtered(lambda l: l.uom_id.id == product.uom_id.id)

            if len(multi_uom_line_id) > 1:
                multi_uom_line_id = multi_uom_line_id[0]

            values['multi_uom_line_id'] = multi_uom_line_id.id

        multi_uom_line_id = self.env['multi.uom.line'].browse(values['multi_uom_line_id'])
        values['multi_uom_qty'] = qty
        values['qty'] = qty * multi_uom_line_id.ratio
        values['multi_uom_price'] = price_unit
        if values['price_unit'] <= 0 or multi_uom_line_id.ratio <= 0:
            values['price_unit'] = 0
        else:
            values['price_unit'] = price_unit / multi_uom_line_id.ratio
        if 'discount' in values:
            values['multi_uom_discount'] = discount
            if values['multi_uom_discount'] <= 0 or multi_uom_line_id.ratio <= 0:
                values['discount'] = 0
            else:
                values['discount'] = discount / multi_uom_line_id.ratio
        return order_line
