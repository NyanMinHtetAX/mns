from odoo import api, models, fields


class ProductPricelist(models.Model):
    _inherit = 'product.pricelist'

    categ_id = fields.Many2one(related='product_id.categ_id', string='Product Category', store=False)
    product_id = fields.Many2one('product.product', 'Product', compute='_compute_product_ids')
    computed_categ_id = fields.Many2one('product.category', string='Computed Category', compute='_compute_categ_id',
                                        store=True)

    @api.depends('item_ids.product_id')
    def _compute_product_ids(self):
        for pricelist in self:
            pricelist.product_id = pricelist.item_ids and pricelist.item_ids[0].product_id.id or False

    @api.depends('product_id')
    def _compute_categ_id(self):
        for record in self:
            record.computed_categ_id = record.product_id.categ_id.id if record.product_id else False

    profit_percent = fields.Float("Profit (%)", compute='_compute_profit_percent', store=True)

    @api.depends('item_ids.profit_percent')
    def _compute_profit_percent(self):
        for pricelist in self:
            profit_percent = 0.0
            if pricelist.item_ids:
                profit_percent = sum(item.profit_percent for item in pricelist.item_ids) / len(pricelist.item_ids)
            pricelist.profit_percent = profit_percent

    def action_tree_view(self):
        return {
            'name': 'Product Pricelists',
            'type': 'ir.actions.act_window',
            'res_model': 'product.pricelist.item',
            'view_mode': 'tree,form',
            'domain': [('id', 'in', self.item_ids.ids)],
        }


class ProductPricelistItem(models.Model):
    _inherit = 'product.pricelist.item'

    item_ids = fields.One2many(
        'product.pricelist.item', 'pricelist_id', 'Pricelist Rules',
        copy=True)
    computed_categ_id = fields.Many2one('product.category', string='Computed Category', compute='_compute_categ_id',
                                        store=True)

    brand_owner = fields.Many2many('res.partner', string='Brand Owner', compute='_compute_brand_owner',
                                   domain=[('supplier', '=', True)], store=True)

    product_uom = fields.Many2one('uom.uom', string='UOM', compute='_compute_uom', store=True)
    final_purchase_price = fields.Float('Final Purchase Price', compute='_compute_final_purchase_price',)


    def _compute_final_purchase_price(self):
        for record in self:
            if record.product_id:
                record.final_purchase_price = record.product_id.final_purchase_price
            else:
                record.final_purchase_price = 0.0

    @api.depends('product_id')
    def _compute_categ_id(self):
        for record in self:
            record.computed_categ_id = record.product_id.categ_id.id if record.product_id else False

    @api.depends('product_id')
    def _compute_brand_owner(self):
        for record in self:
            record.brand_owner = record.product_id.brand_owner.ids if record.product_id else False

    @api.depends('product_id')
    def _compute_uom(self):
        for record in self:
            if record.product_id:
                record.product_uom = record.product_id.uom_id.id
            else:
                record.product_uom = False