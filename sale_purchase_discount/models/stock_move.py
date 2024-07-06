from odoo import api, fields, models, _


class StockMove(models.Model):

    _inherit = "stock.move"

    def _get_price_unit(self):
        """ Returns the unit price for the move"""
        self.ensure_one()
        price_unit = super(StockMove, self)._get_price_unit()

        line = self.purchase_line_id

        if line and self.product_id.id == line.product_id.id:
            price_unit = line.price_unit
            order = line.order_id

            product_qty = 1.0
            if line.discount_type == 'percentage':
                price_unit = price_unit * (1 - (line.discount or 0.0) / 100.0)
            else:
                price_unit = (price_unit * product_qty) - (line.discount * product_qty)

            if line.taxes_id:
                rr = line.taxes_id.with_context(round=False).compute_all(price_unit,
                                                                         currency=line.order_id.currency_id,
                                                                         quantity=1.0)
                price_unit = rr['total_void']

            if line.product_uom.id != line.product_id.uom_id.id:
                price_unit *= line.product_uom.factor / line.product_id.uom_id.factor

            if order.currency_id != order.company_id.currency_id:
                # The date must be today, and not the date of the move since the move move is still
                # in assigned state. However, the move date is the scheduled date until move is
                # done, then date of actual move processing. See:
                # https://github.com/odoo/odoo/blob/2f789b6863407e63f90b3a2d4cc3be09815f7002/addons/stock/models/stock_move.py#L36
                if order.active_currency:
                    price_unit = order.currency_id.with_context(override_currency_rate=order.manual_base_rate)._convert(
                        price_unit, order.company_id.currency_id, order.company_id, fields.Date.context_today(self),
                        round=False)
                else:
                    price_unit = order.currency_id._convert(
                        price_unit, order.company_id.currency_id, order.company_id, fields.Date.context_today(self),
                        round=False)
        return price_unit
