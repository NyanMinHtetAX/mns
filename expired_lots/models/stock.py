from odoo import api, models, fields
from dateutil.relativedelta import relativedelta


class ProductionLot(models.Model):

    _inherit = 'stock.production.lot'

    date_of_expiration = fields.Date('Exp Date')

    def _get_expired_count(self, delta=False, duration=0, unit='days'):
        today = fields.Date.context_today(self)
        if delta:
            lots = self.search([('date_of_expiration', '!=', False),
                                ('date_of_expiration', '>', today)])
            if unit == 'days':
                delta = relativedelta(days=duration)
            elif unit == 'months':
                delta = relativedelta(months=duration)
            else:
                delta = relativedelta(years=duration)
            delta_today = today + delta
            lots = lots.filtered(lambda l: l.date_of_expiration <= delta_today)
        else:
            lots = self.search([('date_of_expiration', '!=', False),
                                ('date_of_expiration', '<=', today)])
        return {'ids': lots.ids, 'count': len(lots)}

    @api.model
    def get_expired_products(self):
        company = self.env.company
        expired_lot_block_a_duration = company.expired_lot_block_a_duration or 15
        expired_lot_block_a_duration_unit = company.expired_lot_block_a_duration_unit or 'days'
        block_a_data = self._get_expired_count(delta=True,
                                               duration=expired_lot_block_a_duration,
                                               unit=expired_lot_block_a_duration_unit)

        expired_lot_block_b_duration = company.expired_lot_block_b_duration or 10
        expired_lot_block_b_duration_unit = company.expired_lot_block_b_duration_unit or 'days'
        block_b_data = self._get_expired_count(delta=True,
                                               duration=expired_lot_block_b_duration,
                                               unit=expired_lot_block_b_duration_unit)

        expired_lot_block_c_duration = company.expired_lot_block_c_duration or 5
        expired_lot_block_c_duration_unit = company.expired_lot_block_c_duration_unit or 'days'
        block_c_data = self._get_expired_count(delta=True,
                                               duration=expired_lot_block_c_duration,
                                               unit=expired_lot_block_c_duration_unit)

        block_d_data = self._get_expired_count(delta=False)
        return {
            'block_a': {
                'color': company.expired_lot_block_a_color or 'rgb(18, 161, 13)',
                'duration': expired_lot_block_a_duration,
                'unit': expired_lot_block_a_duration_unit,
                'count': block_a_data['count'],
                'ids': block_a_data['ids'],
            },
            'block_b': {
                'color': company.expired_lot_block_b_color or 'rgb(9, 157, 186)',
                'duration': expired_lot_block_b_duration,
                'unit': expired_lot_block_b_duration_unit,
                'count': block_b_data['count'],
                'ids': block_b_data['ids'],
            },
            'block_c': {
                'color': company.expired_lot_block_c_color or 'rgb(235, 215, 42)',
                'duration': expired_lot_block_c_duration,
                'unit': expired_lot_block_c_duration_unit,
                'count': block_c_data['count'],
                'ids': block_c_data['ids'],
            },
            'block_d': {
                'color': company.expired_lot_color or 'rgb(168, 10, 26)',
                'count': block_d_data['count'],
                'ids': block_d_data['ids'],
            }
        }
