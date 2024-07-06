import re
from itertools import chain
from decimal import Decimal, ROUND_UP
from odoo import api, fields, models, tools, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools import format_datetime
from datetime import datetime
from odoo.tools.misc import formatLang, get_lang
from odoo.addons.product.models import product_pricelist as OriginalProductPricelist

import math


class ProductPricelist(models.Model):
    _inherit = 'product.pricelist'

    pricelist_item_uom_ids = fields.One2many('pricelist.item.uom', 'pricelist_id', 'Pricelist Item UoM Lines')
    pricelist_uom_id = fields.Many2one('pricelist.item.uom', 'Pricelist Item UOM')

    def _get_pricelist_uom_price(self, product, multi_uom_line, multi_uom_qty):
        items = self.env['product.pricelist.item'].search([('product_id', '=', product.id),
                                                           ('multi_uom_line_id', '=', multi_uom_line.id),
                                                           ('pricelist_id', '=', self.id)])

        if items:
            pricelist_items = []
            for item in items:
                if item.min_quantity <= multi_uom_qty:
                    pricelist_items.append(item.min_quantity)

            min_quantity_sorting = sorted(pricelist_items)
            i = len(min_quantity_sorting)

            price = False
            for item in items:
                if item.date_start and item.date_end:
                    if item.date_start <= datetime.now() <= item.date_end:
                        if item.compute_price == "fixed":
                            if item.min_quantity == min_quantity_sorting[i - 1]:
                                price = item.fixed_price
                        else:
                            if item.base == 'final_purchase_price':
                                if item.min_quantity == min_quantity_sorting[i - 1]:
                                    if item.profit_percent:
                                        percent = round(
                                            (item.profit_percent / 100) * item.product_id.final_purchase_price)
                                        price_percent = round(item.product_id.final_purchase_price,
                                                              2) + item.price_surcharge + item.adjust_amounts
                                        price = (percent + price_percent)
                                    else:
                                        price = round(item.product_id.final_purchase_price,
                                                      2) + item.price_surcharge + item.adjust_amounts
                            else:
                                if item.min_quantity == min_quantity_sorting[i - 1]:
                                    price = item.total_price
                    else:
                        raise ValidationError('!!! Pricelist Validtiy is expired. Please check')
                else:
                    if item.compute_price == "fixed":
                        if item.min_quantity == min_quantity_sorting[i - 1]:
                            price = item.fixed_price
                    else:
                        if item.base == 'final_purchase_price':
                            if item.min_quantity == min_quantity_sorting[i - 1]:
                                if item.profit_percent:
                                    percent = round((item.profit_percent / 100) * item.product_id.final_purchase_price)
                                    price_percent = round(item.product_id.final_purchase_price,
                                                          2) + item.price_surcharge + item.adjust_amounts
                                    price = (percent + price_percent)
                                else:
                                    price = round(item.product_id.final_purchase_price,
                                                  2) + item.price_surcharge + item.adjust_amounts
                        else:
                            if item.min_quantity == min_quantity_sorting[i - 1]:
                                price = item.total_price

            return price
        else:
            if product.detailed_type != 'service':
                raise ValidationError(
                    _('!!! Please Add Pricelist For This Product: ' + product.name)
                )


class PricelistItem(models.Model):
    _inherit = "product.pricelist.item"

    base = fields.Selection(selection_add=[
        ('list_price', 'Sales Price'),
        ('standard_price', 'Cost'),
        ('final_purchase_price', 'Final Purchase Price'),
        ('pricelist', 'Other Pricelist')],
        ondelete={'list_price': 'set default', 'standard_price': 'set default', 'final_purchase_price': 'set default', 'pricelist': 'set default'},
        string="Based on",
        default='pricelist', required=True,
        help='Base price for computation.\n'
             'Sales Price: The base price will be the Sales Price.\n'
             'Cost Price : The base price will be the cost price.\n'
             'Other Pricelist : Computation of the base price based on another Pricelist.')

    base_display = fields.Selection([('final_purchase_price', 'Final Purchase Price'),
                                     ('pricelist', 'Other Pricelist')], "Based on",
                                    default='pricelist', required=True,
                                    help='Final Purchase Price : The base price will be the final purchase price.\n'
                                    'Other Pricelist : Computation of the base price based on another Pricelist.')
    applied_on_display = fields.Selection([
        ('0_product_variant', 'Product')], "Apply On",
        default='0_product_variant', required=True,
        help='Pricelist Item applicable on selected option')
    min_quantity = fields.Float(
        'Min. Quantity', default=1, digits="Product Unit Of Measure",
        help="For the rule to apply, bought/sold quantity must be greater "
             "than or equal to the minimum quantity specified in this field.\n"
             "Expressed in the default unit of measure of the product.")
    compute_price_display = fields.Selection([
        ('fixed', 'Fixed Price'),
        ('formula', 'Formula')], index=True, default='formula', required=True)
    multi_uom_line_id = fields.Many2one('multi.uom.line', 'Multi UoM Line', required=True)
    uom_id = fields.Many2one('uom.uom', related='multi_uom_line_id.uom_id')
    multi_uom_line_ids = fields.Many2many('multi.uom.line', compute='compute_multi_uom_line_ids')
    profit_percent = fields.Float("Profit (%)")
    total_price = fields.Float("Total Price", compute="compute_total_price", store=True)
    product_list_price = fields.Float(related="product_id.product_tmpl_id.list_price", string='Product List Price')
    internal_note = fields.Html(related="product_id.description", string="Product Note")
    adjust_amounts = fields.Float(string='Adjust Amounts')
    round_up = fields.Selection([
        ('default', 'Default'),
        ('ten', 'Ten Digits'),
        ('hundred', 'Hundred Digits'),
    ], string='Round Up', copy=False, index=True, default='default')
    fixed_price = fields.Float('Fixed Price', digits='Product Price', compute="_compute_fixed_price")

    @api.depends('total_price')
    def _compute_fixed_price(self):
        for item in self:
            item.fixed_price = item.total_price

    @api.onchange('round_up')
    def onchange_round_up(self):
        for rec in self:
            if rec.round_up == 'ten':
                rec.total_price = self._origin.total_price
                total_price = str(rec.total_price)
                last_index = int(total_price[len(str(int(rec.total_price))) - 1])
                last_value = rec.compute_add_value(last_index, 10)
                rec.total_price = rec.total_price + last_value
            elif rec.round_up == 'hundred':
                rec.total_price = self._origin.total_price
                total_price = str(rec.total_price)
                last_index = int(total_price[len(str(int(rec.total_price))) - 1])
                last_second_index = int(total_price[len(str(int(rec.total_price))) - 2])
                real_last_index = int(str(last_second_index) + str(last_index))
                last_value = rec.compute_add_value(real_last_index, 100)
                rec.total_price = rec.total_price + last_value
            else:
                rec.total_price = self._origin.total_price

    def compute_add_value(self, real_last_index, value):
        last_value = value - real_last_index
        if last_value != 10 and last_value != 100:
            return last_value
        else:
            return 0

    @api.depends('applied_on', 'categ_id', 'product_tmpl_id', 'product_id', 'compute_price', 'fixed_price',
                 'pricelist_id', 'percent_price', 'price_discount', 'price_surcharge')
    def _get_pricelist_item_name_price(self):
        for item in self:
            if item.categ_id and item.applied_on == '2_product_category':
                item.name = _("Category: %s") % (item.categ_id.display_name)
            elif item.product_tmpl_id and item.applied_on == '1_product':
                item.name = _("Product: %s") % (item.product_tmpl_id.display_name)
            elif item.product_id and item.applied_on == '0_product_variant':
                item.name = _("Variant: %s") % (item.product_id.with_context(display_default_code=False).display_name)
            else:
                item.name = _("All Products")

            if item.compute_price == 'fixed':
                item.price = formatLang(item.env, item.fixed_price, monetary=True, dp="Product Price",
                                        currency_obj=item.currency_id)
            elif item.compute_price == 'percentage':
                item.price = _("%s %% discount", item.percent_price)
            else:
                item.price = _("%(percentage)s %% profit and %(price)s landed cost", percentage=item.profit_percent,
                               price=item.price_surcharge)

    OriginalProductPricelist._get_pricelist_item_name_price = _get_pricelist_item_name_price

    @api.onchange('base_display')
    def change_base(self):
        for rec in self:
            rec.base = rec.base_display

    @api.onchange('applied_on_display')
    def change_applied_on(self):
        for rec in self:
            rec.applied_on = rec.applied_on_display

    @api.onchange('compute_price_display')
    def change_compute_price(self):
        for rec in self:
            rec.compute_price = rec.compute_price_display

    @api.depends('compute_price', 'multi_uom_line_id', 'product_id', 'product_id.final_purchase_price',
                 'price_surcharge', 'base', 'profit_percent',
                 'base_pricelist_id', 'base_pricelist_id.item_ids', 'adjust_amounts')
    @api.depends_context('force_recompute')
    def compute_total_price(self):
        price = False
        for item in self:
            item.invalidate_cache(['total_price'])
            if item.compute_price == "fixed":
                item.total_price = item.fixed_price
            else:
                if item.base == 'final_purchase_price':

                    if item.profit_percent:

                        percent = round((item.profit_percent / 100) * item.product_id.final_purchase_price)
                        price = round(item.product_id.final_purchase_price,
                                      2) + item.price_surcharge + item.adjust_amounts
                        # item.total_price = round(price + (price * (item.profit_percent / 100)))
                        item.total_price = (percent + price)
                    else:
                        item.total_price = round(item.product_id.final_purchase_price,
                                                 2) + item.price_surcharge + item.adjust_amounts
                else:
                    if item.base_pricelist_id.item_ids:
                        default_uom_id = item.product_id.multi_uom_line_ids.filtered(lambda l: l.is_default_uom == True)
                        if item.multi_uom_line_id == default_uom_id:
                            for rec in item.base_pricelist_id.item_ids:
                                if item.product_id == rec.product_id:
                                    default_uom_id = item.product_id.multi_uom_line_ids.filtered(
                                        lambda l: l.is_default_uom == True)

                                    try:
                                        item.total_price = round(
                                            rec.total_price * (item.multi_uom_line_id.ratio / default_uom_id.ratio))
                                    except:
                                        pass
                                    if item.profit_percent:
                                        percent = round(
                                            (item.profit_percent / 100) * item.total_price)
                                        price = round(item.total_price,
                                                      2) + item.price_surcharge + item.adjust_amounts
                                        # item.total_price = round(price + (price * (item.profit_percent / 100)))
                                        item.total_price = (percent + price)
                                        # price = item.total_price + item.price_surcharge
                                        # item.total_price = round(price + (price * (item.profit_percent / 100)))
                                        break
                                    else:
                                        item.total_price = round(item.total_price,
                                                                 2) + item.price_surcharge + item.adjust_amounts
                                        # item.total_price = item.total_price + item.price_surcharge
                                        break
                                else:
                                    item.total_price = 0.0
                        else:
                            if item.min_quantity == 1:
                                for rec in item.base_pricelist_id.item_ids:
                                    if item.product_id == rec.product_id:
                                        default_uom_id = item.product_id.multi_uom_line_ids.filtered(
                                            lambda l: l.is_default_uom == True)

                                        try:
                                            item.total_price = round(
                                                rec.total_price * (item.multi_uom_line_id.ratio / default_uom_id.ratio))
                                        except:
                                            pass
                                        if item.profit_percent:
                                            percent = round(
                                                (item.profit_percent / 100) * item.total_price)
                                            price = round(item.total_price,
                                                          2) + item.price_surcharge + item.adjust_amounts
                                            # item.total_price = round(price + (price * (item.profit_percent / 100)))
                                            item.total_price = (percent + price)
                                            # price = item.total_price + item.price_surcharge
                                            # item.total_price = round(price + (price * (item.profit_percent / 100)))
                                            break
                                        else:
                                            item.total_price = round(item.total_price,
                                                                     2) + item.price_surcharge + item.adjust_amounts
                                            break
                                    else:
                                        item.total_price = 0.0
                            else:

                                for rec in item.base_pricelist_id.item_ids:
                                    if item.product_id == rec.product_id:
                                        default_uom_id = rec.product_id.multi_uom_line_ids.filtered(
                                            lambda l: l.is_default_uom == True)

                                        try:
                                            item.total_price = round(
                                                rec.total_price * (item.multi_uom_line_id.ratio / default_uom_id.ratio))
                                        except:
                                            pass

                                        if item.profit_percent:
                                            percent = round(
                                                (item.profit_percent / 100) * item.total_price)
                                            price = round(item.total_price,
                                                          2) + item.price_surcharge + item.adjust_amounts
                                            # item.total_price = round(price + (price * (item.profit_percent / 100)))
                                            item.total_price = (percent + price)
                                            # price = item.total_price + item.price_surcharge
                                            # item.total_price = round(price + (price * (item.profit_percent / 100)))
                                            break
                                        else:
                                            # item.total_price = (item.total_price + item.price_surcharge)
                                            item.total_price = round(item.total_price,
                                                                     2) + item.price_surcharge + item.adjust_amounts
                                            break
                                    else:
                                        item.total_price = 0.0

                    else:
                        item.total_price = 0.0

    @api.depends_context('lang')
    @api.depends('compute_price', 'price_discount', 'price_surcharge', 'base', 'price_round')
    def _compute_rule_tip(self):
        base_selection_vals = {elem[0]: elem[1] for elem in self._fields['base']._description_selection(self.env)}
        self.rule_tip = False
        for item in self:
            if item.compute_price != 'formula':
                continue
            base_amount = 100
            discount_factor = item.profit_percent / 100
            total_base = base_amount + item.price_surcharge
            discounted_price = total_base + (total_base * discount_factor)

            if item.price_round:
                discounted_price = tools.float_round(discounted_price, precision_rounding=item.price_round)
            surcharge = tools.format_amount(item.env, item.price_surcharge, item.currency_id)
            item.rule_tip = _(
                "%(base)s with a %(discount)s %% Profit and %(surcharge)s Landed Cost\n"
                "Example: %(amount)s  + %(price_surcharge)s * %(discount_charge)s → %(total_amount)s",
                base=base_selection_vals[item.base],
                discount=item.profit_percent,
                surcharge=surcharge,
                amount=tools.format_amount(item.env, 100, item.currency_id),
                discount_charge=discount_factor,
                price_surcharge=surcharge,
                total_amount=tools.format_amount(
                    item.env, discounted_price, item.currency_id),
            )

    @api.depends('product_tmpl_id', 'product_id')
    def compute_multi_uom_line_ids(self):
        for rec in self:
            if rec.compute_price == "fixed":
                rec.multi_uom_line_ids = rec.product_id.multi_uom_line_ids.ids
            else:
                if not rec.base == "pricelist":
                    rec.multi_uom_line_ids = rec.product_id.multi_uom_line_ids.filtered(
                        lambda l: l.is_default_uom == True)
                    rec.multi_uom_line_id = rec.product_id.multi_uom_line_ids.filtered(
                        lambda l: l.is_default_uom == True)
                else:
                    rec.multi_uom_line_ids = rec.product_id.multi_uom_line_ids.ids
                    if not rec.multi_uom_line_id:
                        rec.multi_uom_line_id = rec.product_id.multi_uom_line_ids.filtered(
                            lambda l: l.is_default_uom == True)


class PricelistItemUom(models.Model):
    _name = 'pricelist.item.uom'
    _description = 'UoM Pricelist Item'

    product_id = fields.Many2one('product.product', 'Product', required=True)
    product_tmpl_id = fields.Many2one('product.template',
                                      string='Multi UoM Lines',
                                      related='product_id.product_tmpl_id',
                                      required=True)
    multi_uom_line_id = fields.Many2one('multi.uom.line', 'Multi UoM Line', required=True)
    uom_id = fields.Many2one('uom.uom', related='multi_uom_line_id.uom_id')
    price = fields.Float('Price', required=True)
    current_company_id = fields.Many2one('res.company', default=lambda self: self.env.company)
    currency_id = fields.Many2one('res.currency', string='Currency', related='current_company_id.currency_id',
                                  readonly=True)
    pricelist_id = fields.Many2one('product.pricelist', 'Pricelist', ondelete='cascade')
    pricelist_qty = fields.Float('Quantity')

    # @api.constrains('product_id', 'multi_uom_line_id', 'pricelist_id')
    # def _check_duplicate_record(self):
    #     for rec in self:
    #         duplicate = self.search([('product_id', '=', rec.product_id.id),
    #                                  ('multi_uom_line_id', '=', rec.multi_uom_line_id.id),
    #                                  ('pricelist_id', '=', rec.pricelist_id.id),
    #                                  ('id', '!=', rec.id)])
    #         if duplicate:
    #             raise ValidationError(f'Record already exists.\n\nName - {rec.product_id.name}'
    #                                   f'\nUoM - {rec.multi_uom_line_id.uom_id.name}\nPricelist - {rec.pricelist_id.name}')
