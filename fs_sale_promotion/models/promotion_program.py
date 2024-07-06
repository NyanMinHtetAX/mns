import math
from odoo import api, models, fields
from odoo.exceptions import ValidationError

OPERATOR = [('=', 'Equal'), ('>=', 'Greater than OR Equal')]
DISCOUNT_TYPE = [('fixed_disc', 'Fixed Discount'), ('percent_disc', 'Percentage Discount')]
REWARD_TYPE = [('fixed_disc', 'Fixed Discount'), ('percent_disc', 'Percentage Discount'), ('foc', 'FOC Product')]


class OrderLine:

    def __init__(self, id, product_id, qty, uom, price, subtotal):
        self.id = id
        self.product_id = product_id
        self.qty = qty * uom.ratio
        self.uom = uom
        self.price = price * uom.ratio
        self.subtotal = subtotal

    @staticmethod
    def mapped(self, attribute):
        data = []
        for obj in self:
            data.append(getattr(obj, attribute))
        return data


class Reward:

    def __init__(self, product_id, qty, promotion_id, price=0, account_id=False, description='',promotion_type=False):
        self.product_id = product_id
        self.qty = qty
        self.price = price
        self.promotion_id = promotion_id
        self.account_id = account_id
        self.description = description
        self.promotion_type= promotion_type


class LineDiscount:

    def __init__(self, line_id, type, discount, promotion_id):
        self.line_id = line_id
        self.type = type
        self.discount = discount
        self.promotion_id = promotion_id


class PromotionProgram(models.Model):

    _name = 'promotion.program'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Promotion Program'

    name = fields.Char('Name', required=1)
    type = fields.Selection([('buy_x_get_y', 'Buy X Get Y Free'),
                             ('disc_on_total_amt', 'Discount on Total Amount'),
                             ('disc_on_qty', 'Discount on Product Quantity'),
                             ('disc_multi_catego', 'Discount on Multi Categories'),
                             ('disc_comb_prods', 'Discount on Combination Products'),
                             ('disc_comb_prods_qty', 'Discount on Combination Products Quantity'),
                             ('promo_based_price_segment_combi', 'Based on Price Segment Combination Items'),
                             ('promo_based_price_segment_multi', 'Based on Price Segment Multi')],
                            string='Promotion Type',
                            required=1,
                            default='buy_x_get_y')
    promo_code = fields.Char('Promo Code')
    use_promo_code = fields.Boolean('Use Promo Code')
    active = fields.Boolean('Active', default=True)
    start_date = fields.Date('Start Date')
    end_date = fields.Date('End Date')
    disc_on_combination_qty_total_qty = fields.Float('Total Qty')
    price_range_based_on = fields.Selection([('category', 'Category'),
                                             ('product', 'Product')], 'Price Range Based On', default='category')
    buy_x_get_y_line_ids = fields.One2many('buy.x.get.y.line', 'promotion_id', 'Buy X Get Y Lines')
    disc_on_qty_line_ids = fields.One2many('discount.on.qty.line', 'promotion_id', 'Disc On Qty Lines')
    disc_on_combination_line_ids = fields.One2many('discount.on.combination.line', 'promotion_id', 'Disc On Combination Lines')
    disc_on_combination_qty_line_ids = fields.One2many('discount.on.combination.qty.line', 'promotion_id', 'Disc On Combination Qty Lines')
    disc_on_price_and_combination_line_ids = fields.One2many('discount.on.price.range.combination', 'promotion_id', 'Disc On Price Range & Combination Lines')
    disc_on_price_range_multi_line_ids = fields.One2many('discount.on.price.range.multi', 'promotion_id', 'Disc On Price Range Multi Lines')
    team_ids = fields.Many2many('crm.team', 'promotion_sale_team_rel', 'promotion_id', 'team_id', 'Sale Teams')
    company_id = fields.Many2one('res.company', 'Company', default=lambda self: self.env.company.id, required=1)

    # disc_multi_catego
    category_ids = fields.Many2many('product.category', string='Categories')
    multi_category_discount_type = fields.Selection(DISCOUNT_TYPE, string='Discount Type')
    multi_category_discount = fields.Float('Category Discount')
    multi_category_discount_product_id = fields.Many2one('product.product', 'Discount Product', domain=[('detailed_type', '=', 'service')])

    # disc_on_total_amt
    order_amount = fields.Float('Total Invoice Amount')
    operator = fields.Selection(OPERATOR, 'Operator', default='=')
    reward_type = fields.Selection(REWARD_TYPE, 'Offer Type')
    discount = fields.Float('Discount')
    account_id = fields.Many2one('account.account', 'COA')
    product_id = fields.Many2one('product.product', 'Disc Product (OR) Offer Product')

    def toggle_active(self):
        for program in self:
            program.write({'active': not program.active})

    @api.constrains('type', 'buy_x_get_y_line_ids', 'disc_on_qty_line_ids', 'disc_on_combination_line_ids')
    def _validate_program(self):
        for program in self:
            if program.type == 'buy_x_get_y' and not program.buy_x_get_y_line_ids:
                raise ValidationError('Please add at least one line.')
            elif program.type == 'disc_on_qty' and not program.disc_on_qty_line_ids:
                raise ValidationError('Please add at least one line.')
            elif program.type == 'disc_comb_prods' and not program.disc_on_combination_line_ids:
                raise ValidationError('Please add at least one line.')
            elif program.type == 'promo_based_price_segment_combi' and not program.disc_on_price_and_combination_line_ids:
                raise ValidationError('Please add at least one line.')
            elif program.type == 'promo_based_price_segment_multi' and not program.disc_on_price_range_multi_line_ids:
                raise ValidationError('Please add at least one line.')

    def _get_available_programs(self, date, team):
        available_programs = self.browse()
        programs = self.search([('use_promo_code', '=', False)]).filtered(lambda p: team.id in p.team_ids.ids)
        for program in programs:
            if program.start_date and program.end_date and program.start_date <= date <= program.end_date:
                available_programs |= program
            elif program.start_date and not program.end_date and date >= program.start_date:
                available_programs |= program
            elif program.end_date and not program.start_date and date <= program.end_date:
                available_programs |= program
            elif not program.start_date and not program.end_date:
                available_programs |= program
        return available_programs

    def _apply_buy_x_get_y(self, lines, order_amount):
        rewards = []
        self.ensure_one()
        promotion_lines = self.buy_x_get_y_line_ids
        for line in lines:
            applicable_lines = promotion_lines.filtered(
                lambda l: l.product_x_id.id == line.product_id and l.product_x_qty <= line.qty
            )
            if not applicable_lines:
                continue
            if applicable_lines[-1].operator == '=':
                qty = math.floor(line.qty / applicable_lines[-1].product_x_qty) * applicable_lines[-1].product_y_qty
            else:
                qty = applicable_lines[-1].product_y_qty
            product = self.env['product.product'].browse(line.product_id)
            description = f'FOC Product for purchasing {product.name}'
            rewards.append(Reward(product_id=applicable_lines[-1].product_y_id.id,
                                  qty=qty,
                                  promotion_id=self.id,
                                  account_id=applicable_lines[-1].promotion_account_id.id,
                                  description=description))
        return rewards

    def _apply_disc_on_total_amt(self, lines, order_amount):
        rewards = []
        self.ensure_one()
        if order_amount < self.order_amount:
            return rewards
        reward_type = 'Discount'
        product_qty = 1
        qty = math.floor(order_amount / self.order_amount)
        if self.reward_type == 'fixed_disc':
            if self.operator == '=':
                price = self.discount * qty * -1
            else:
                price = self.discount * -1
        elif self.reward_type == 'percent_disc':
            price = order_amount * (self.discount / 100) * -1
        else:
            reward_type = 'FOC Product'
            product_qty = qty if self.operator == '=' else 1
            price = 0
        description = f'{reward_type} for purchasing more than {self.order_amount}'
        rewards.append(Reward(product_id=self.product_id.id,
                              qty=product_qty,
                              price=price,
                              promotion_id=self.id,
                              account_id=self.account_id.id,
                              description=description,
                              promotion_type=self.reward_type))
        return rewards

    def _apply_disc_on_qty(self, lines, order_amount):
        rewards = []
        self.ensure_one()
        promotion_lines = self.disc_on_qty_line_ids
        for line in lines:
            applicable_lines = promotion_lines.filtered(
                lambda l: l.product_id.id == line.product_id and l.qty <= line.qty
            )
            if not applicable_lines:
                continue
            applicable_line = applicable_lines[-1]
            if applicable_line.discount_type == 'fixed_disc':
                if applicable_line.operator == '=':
                    qty = math.floor(line.qty / applicable_line.qty)
                else:
                    qty = 1
                discount = applicable_line.discount_amt * qty
            else:
                discount = line.subtotal * (applicable_line.discount_amt / 100)
            description = f'Discount for purchasing {applicable_line.product_id.name}'
            rewards.append(Reward(product_id=applicable_line.promotion_product_id.id,
                                  qty=1,
                                  price=discount * -1,
                                  promotion_id=self.id,
                                  description=description))
        return rewards

    def _apply_disc_multi_catego(self, lines, order_amount):
        rewards = []
        self.ensure_one()
        promotion_product_ids = self.env['product.product'].search([('categ_id', 'in', self.category_ids.ids)])
        applicable_lines = [line for line in lines if line.product_id in promotion_product_ids.ids]
        if len(applicable_lines) > 0:
            total = sum(OrderLine.mapped(applicable_lines, 'subtotal'))
            if self.multi_category_discount_type == 'fixed_disc':
                discount = self.multi_category_discount
            else:
                discount = total * (self.multi_category_discount / 100)
            products = self.env['product.product'].browse(OrderLine.mapped(applicable_lines, 'product_id'))
            description = 'Discount for purchasing ' + ', '.join([product.name for product in products])
            rewards.append(Reward(product_id=self.multi_category_discount_product_id.id,
                                  qty=1,
                                  price=discount * -1,
                                  promotion_id=self.id,
                                  description=description))
        return rewards

    def _apply_disc_comb_prods(self, lines, order_amount):
        rewards = []
        self.ensure_one()
        promotion_lines = self.disc_on_combination_line_ids
        for line in promotion_lines:
            promotion_product_ids = set(line.product_ids.ids)
            order_product_ids = set(OrderLine.mapped(lines, 'product_id'))
            if promotion_product_ids.issubset(order_product_ids):
                if line.discount_type == 'fixed_disc':
                    # min_qty = min(OrderLine.mapped(lines, 'qty'))  I have no idea why I did this way.
                    #                                                Just commenting 'cause it doesn't make sense.
                    discount = line.discount_amt
                else:
                    subtotal = sum(l.subtotal for l in lines if l.product_id in line.product_ids.ids)
                    discount = subtotal * (line.discount_amt / 100)
                description = f'Discount for purchasing {", ".join(line.product_ids.mapped("name"))}'
                rewards.append(Reward(product_id=line.promotion_product_id.id,
                                      qty=1,
                                      price=discount * -1,
                                      promotion_id=self.id,
                                      description=description))
        return rewards

    def _apply_disc_comb_prods_qty(self, lines, order_amount):
        rewards = []
        self.ensure_one()
        promotion_lines = self.disc_on_combination_qty_line_ids
        promotion_product_ids = set(self.disc_on_combination_qty_line_ids.product_id.ids)
        order_product_ids = set(OrderLine.mapped(lines, 'product_id'))
        total_qty = sum(l.qty for l in lines if l.product_id in promotion_product_ids)
        if total_qty < self.disc_on_combination_qty_total_qty or not promotion_product_ids.issubset(order_product_ids):
            return rewards
        for promotion_line in promotion_lines:
            order_lines = [l for l in lines if l.product_id == promotion_line.product_id.id]
            product_qty = sum(OrderLine.mapped(order_lines, 'qty'))
            product_subtotal = sum(OrderLine.mapped(order_lines, 'subtotal'))
            if product_qty < promotion_line.min_qty:
                rewards = []
                break
            if promotion_line.discount_type == 'fixed_disc':
                discount = promotion_line.discount
            else:
                discount = product_subtotal * (promotion_line.discount / 100)
            description = f'Discount for purchasing {promotion_line.product_id.name}'
            rewards.append(Reward(product_id=promotion_line.promotion_product_id.id,
                                  qty=1,
                                  price=discount * -1,
                                  promotion_id=self.id,
                                  description=description))
        return rewards

    def _apply_promo_based_price_segment_combi(self, lines, order_amount):
        rewards = []
        self.ensure_one()
        promotion_lines = self.disc_on_price_and_combination_line_ids
        for line in promotion_lines:
            promotion_product_ids = set(line.product_ids.ids)
            order_product_ids = set(OrderLine.mapped(lines, 'product_id'))
            if not promotion_product_ids.issubset(order_product_ids):
                continue
            amount = sum(l.subtotal for l in lines if l.product_id in line.product_ids.ids)
            if not (line.price_range_from <= amount <= line.price_range_to):
                continue
            reward_type = 'Discount'
            if line.reward_type == 'fixed_disc':
                price = line.discount * -1
            elif line.reward_type == 'percent_disc':
                price = amount * (line.discount / 100) * -1
            else:
                reward_type = 'FOC Product'
                self.reward_type = 'foc'
                price = 0
            description = f'{reward_type} for purchasing {", ".join(line.product_ids.mapped("name"))}'
            rewards.append(Reward(product_id=line.promotion_product_id.id,
                                  qty=1,
                                  price=price,
                                  promotion_id=self.id,
                                  account_id=line.account_id.id,
                                  description=description,
                                  promotion_type=self.reward_type))
        return rewards

    def _apply_promo_based_price_segment_multi(self, lines, order_amount):
        rewards = []
        self.ensure_one()
        promotion_lines = self.disc_on_price_range_multi_line_ids
        for line in promotion_lines:
            if self.price_range_based_on == 'product':
                product_ids = line.product_id.ids
            else:
                product_ids = self.env['product.product'].search([('categ_id', '=', line.category_id.id)]).ids
            applicable_lines = [l for l in lines if l.product_id in product_ids]
            total_qty = sum(OrderLine.mapped(applicable_lines, 'qty'))
            amount = sum(OrderLine.mapped(applicable_lines, 'subtotal'))
            if not (line.price_range_from <= amount <= line.price_range_to):
                continue
            reward_type = 'Discount'
            if line.reward_type == 'fixed_disc':
                price = line.discount * -1
            elif line.reward_type == 'percent_disc':
                price = amount * (line.discount / 100) * -1
            else:
                reward_type = 'FOC Product'
                self.reward_type = 'foc'
                price = 0
            applicable_products = self.env['product.product'].browse(OrderLine.mapped(applicable_lines, 'product_id'))
            description = f'{reward_type} for purchasing {", ".join(applicable_products.mapped("name"))}'
            rewards.append(Reward(product_id=line.promotion_product_id.id,
                                  qty=1,
                                  price=price,
                                  promotion_id=self.id,
                                  account_id=line.account_id.id,
                                  description=description,
                                  promotion_type=self.reward_type))
        return rewards


class BuyXGetYLine(models.Model):

    _name = 'buy.x.get.y.line'
    _description = 'Buy X Get Y Line'
    _order = 'product_x_id, product_x_qty'

    product_x_id = fields.Many2one('product.product', 'Product (X)', required=1)
    product_x_qty = fields.Float('Product (X) Qty', required=1)
    operator = fields.Selection(OPERATOR, 'Operator', required=1, default='=')
    product_y_id = fields.Many2one('product.product', 'Product (Y)', required=1)
    product_y_qty = fields.Float('Product (Y) Qty', required=1)
    promotion_account_id = fields.Many2one('account.account', 'COA')
    promotion_id = fields.Many2one('promotion.program', 'Promotion', ondelete='cascade')

    @api.constrains('product_x_qty', 'product_y_qty')
    def _validate_line(self):
        for line in self:
            if line.product_x_qty == 0 or line.product_y_qty == 0:
                raise ValidationError('Quantities can\'t be zero.')


class DiscOnQty(models.Model):

    _name = 'discount.on.qty.line'
    _description = 'Discount on Qty Line'
    _order = 'product_id, qty'

    product_id = fields.Many2one('product.product', 'Product', required=1)
    operator = fields.Selection(OPERATOR, 'Operator', required=1, default='=')
    qty = fields.Float('Qty', required=1)
    discount_type = fields.Selection(DISCOUNT_TYPE, default='fixed_disc', required=1)
    discount_amt = fields.Float('Discount Amount', required=1)
    promotion_product_id = fields.Many2one('product.product', 'Discount Product',
                                           domain=[('detailed_type', '=', 'service')],
                                           required=1)
    promotion_id = fields.Many2one('promotion.program', 'Promotion', ondelete='cascade')

    @api.constrains('qty', 'discount_amt')
    def _validate_line(self):
        for line in self:
            if line.qty == 0:
                raise ValidationError('Qty can\'t be zero.')
            elif line.discount_amt == 0:
                raise ValidationError('Discount amount can\'t be zero.')


class DiscOnCombinationLine(models.Model):

    _name = 'discount.on.combination.line'
    _description = 'Discount on Combination Line'

    product_ids = fields.Many2many('product.product', string='Products', required=1)
    discount_type = fields.Selection(DISCOUNT_TYPE, default='fixed_disc', required=1)
    discount_amt = fields.Float('Discount Amount', required=1)
    promotion_product_id = fields.Many2one('product.product', 'Discount Product',
                                           domain=[('detailed_type', '=', 'service')],
                                           required=1)
    promotion_id = fields.Many2one('promotion.program', 'Promotion', ondelete='cascade')


class DiscOnCombinationQtyLine(models.Model):

    _name = 'discount.on.combination.qty.line'
    _description = 'Discount on Qty Combination Line'

    product_id = fields.Many2one('product.product', string='Products', required=1)
    min_qty = fields.Float('Min Qty', required=1)
    discount_type = fields.Selection(DISCOUNT_TYPE, default='fixed_disc', required=1)
    discount = fields.Float('Discount Amount', required=1)
    promotion_product_id = fields.Many2one('product.product', 'Discount Product',
                                           domain=[('detailed_type', '=', 'service')],
                                           required=1)
    promotion_id = fields.Many2one('promotion.program', 'Promotion', ondelete='cascade')


class DiscOnPriceRangeCombination(models.Model):

    _name = 'discount.on.price.range.combination'
    _description = 'Discount on Price Range Combination'

    product_ids = fields.Many2many('product.product', string='Products', required=1)
    price_range_from = fields.Float('Price From', required=1)
    price_range_to = fields.Float('Price To', required=1)
    reward_type = fields.Selection(REWARD_TYPE, 'Offer Type', default='fixed_disc', required=1)
    discount = fields.Float('Discount', required=1)
    promotion_product_id = fields.Many2one('product.product', 'Promotion Product', required=1)
    account_id = fields.Many2one('account.account', 'COA')
    promotion_id = fields.Many2one('promotion.program', 'Promotion', ondelete='cascade')

    @api.constrains('price_range_from', 'price_range_to')
    def _validate_line(self):
        for line in self:
            if line.price_range_from == 0 or line.price_range_to == 0:
                raise ValidationError('Prices can\'t be zero.')
            elif line.price_range_from > line.price_range_to:
                raise ValidationError('Price from can\'t be greater than price to.')


class DiscOnPriceRangeMulti(models.Model):

    _name = 'discount.on.price.range.multi'
    _description = 'Discount on Price Range Multi'

    product_id = fields.Many2one('product.product', string='Product', required=0)
    category_id = fields.Many2one('product.category', string='Category', required=0)
    price_range_from = fields.Float('Price From', required=1)
    price_range_to = fields.Float('Price To', required=1)
    reward_type = fields.Selection(REWARD_TYPE, 'Offer Type', default='fixed_disc', required=1)
    discount = fields.Float('Discount', required=1)
    promotion_product_id = fields.Many2one('product.product', 'Promotion Product', required=1)
    account_id = fields.Many2one('account.account', 'COA')
    promotion_id = fields.Many2one('promotion.program', 'Promotion', ondelete='cascade')

    @api.constrains('price_range_from', 'price_range_to')
    def _validate_line(self):
        for line in self:
            if line.price_range_from == 0 or line.price_range_to == 0:
                raise ValidationError('Prices can\'t be zero.')
            elif line.price_range_from > line.price_range_to:
                raise ValidationError('Price from can\'t be greater than price to.')
