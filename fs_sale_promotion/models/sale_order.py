from odoo import api, models, fields
from odoo.addons.fs_sale_promotion.models.promotion_program import OrderLine, LineDiscount, Reward


class SaleOrder(models.Model):

    _inherit = 'sale.order'

    available_promotions = fields.Many2many('promotion.program', string='Available Promotions', compute='_compute_available_promotions')

    def _compute_available_promotions(self):
        for order in self:
            if order.date_order:
                programs = self.env['promotion.program']._get_available_programs(order.date_order.date(), order.team_id)
                order.available_promotions = [(6, 0, programs.ids)]
            else:
                order.available_promotions = []

    def btn_apply_promotion_program(self):
        rewards = {}
        applied_promotions = False
        self.remove_promotions()
        lines = [OrderLine(line.id,
                           line.product_id.id,
                           line.multi_uom_qty,
                           line.multi_uom_line_id,
                           self.currency_id._convert(line.multi_price_unit,
                                                     self.company_id.currency_id,
                                                     self.company_id,
                                                     self.date_order.date()),
                           self.currency_id._convert(line.price_subtotal,
                                                     self.company_id.currency_id,
                                                     self.company_id,
                                                     self.date_order.date()),
                           ) for line in self.order_line]
        order_amount = self.currency_id._convert(self.amount_total,
                                                 self.company_id.currency_id,
                                                 self.company_id,
                                                 self.date_order.date())
        self._compute_available_promotions()
        for promotion in self.available_promotions:
            method = getattr(promotion, f'_apply_{promotion.type}')
            promotion_rewards = method(lines, order_amount)
            if promotion_rewards:
                rewards[promotion.id] = promotion_rewards
        lines_to_create = []
        for key, promotion_rewards in rewards.items():
            for reward in promotion_rewards:
                applied_promotions = True
                if type(reward) == Reward:
                    promotion = self.env['promotion.program'].browse(reward.promotion_id)
                    product = self.env['product.product'].browse(reward.product_id)
                    multi_uom_line_id = product.multi_uom_line_ids.filtered(lambda l: l.uom_id.id == product.uom_id.id)
                    price = self.company_id.currency_id._convert(reward.price,
                                                                 self.currency_id,
                                                                 self.company_id,
                                                                 self.date_order.date())
                    if reward.promotion_type =='foc':
                        
                        values = {
                            'name': reward.description,
                            'product_id': reward.product_id,
                            'multi_uom_line_id': multi_uom_line_id.id,
                            'multi_price_unit': price,
                            'price_unit': price,
                            'multi_uom_qty': reward.qty,
                            'product_uom_qty': reward.qty,
                            'order_id': self.id,
                            'is_foc': True,
                            'price_subtotal': 0,
                            'promotion_id': reward.promotion_id,
                            'tax_id': False,
                            'promotion_account_id': reward.account_id,
                            'sequence': 1000,
                        }
                    else:
                        values = {
                            'name': reward.description,
                            'product_id': reward.product_id,
                            'multi_uom_line_id': multi_uom_line_id.id,
                            'multi_price_unit': price,
                            'price_unit': price,
                            'multi_uom_qty': reward.qty,
                            'product_uom_qty': reward.qty,
                            'order_id': self.id,
                            'is_foc': False,
                            'price_subtotal': 0,
                            'promotion_id': reward.promotion_id,
                            'tax_id': False,
                            'promotion_account_id': reward.account_id,
                            'sequence': 1000,
                        }
                    lines_to_create.append(values)
                elif type(reward) == LineDiscount:

                    line = self.env['sale.order.line'].browse(reward.line_id)
                    line.update({
                        'discount_type': reward.type,
                        'price_subtotal': price,
                        'is_foc': False,
                        'multi_uom_discount': reward.discount,
                    })
        self.env['sale.order.line'].create(lines_to_create)
        if applied_promotions:
            return {
                'effect': {
                    'type': 'rainbow_man',
                    'message': 'Promotions applied.',
                }
            }

    def remove_promotions(self):
        promotion_lines = self.order_line.filtered(lambda l: l.promotion_id)
        promotion_lines.unlink()


class SaleOrderLine(models.Model):

    _inherit = 'sale.order.line'

    promotion_id = fields.Many2one('promotion.program', 'Promotion')
    promotion_account_id = fields.Many2one('account.account', 'Promotion COA')

    def _prepare_invoice_line(self, **optional_values):
        values = super(SaleOrderLine, self)._prepare_invoice_line(**optional_values)
        values['promotion_id'] = self.promotion_id.id
        values['promotion_account_id'] = self.promotion_account_id.id
        return values
