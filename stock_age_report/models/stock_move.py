from odoo import models, fields, api


class StockMove(models.Model):
    _inherit = 'stock.move'

    out_qtys = fields.Integer(default=0, string='OutMove Qtys')
    remaining_qtys = fields.Integer(default=0, string='Remaining Qtys')
    multi_uom_remaining_qtys = fields.Char(string='Remaining Qtys')

    def update_out_and_remaining_qtys(self):
        # Update for all non-updated moves
        moves = self.env['stock.move'].search([('remaining_qtys', '=', 0)])

        print("moves", len(moves))
        for record in moves:
            print('record', record)
            # Get All outmoves (Sale, Adj out, Scrap)
            out_domain = [
                ('product_id', '=', record.product_id.id),
                ('state', '=', 'done'), ('location_id.usage', '=', 'internal'),
                ('location_id', '=', record.location_id.id),
                # Not include purchase in/out moves
                ('purchase_line_id', '=', False)
            ]
            out_return_domain = [
                ('product_id', '=', record.product_id.id),
                ('state', '=', 'done'), ('location_id.usage', '!=', 'internal'),
                ('location_dest_id', '=', record.location_id.id),
                ('purchase_line_id', '=', False), ('to_refund', '=', True)

            ]
            transfer_domain = [
                ('product_id', '=', record.product_id.id),
                ('state', '=', 'done'), ('location_id.usage', '=', 'internal'),
                ('location_dest_id', '=', record.location_id.id),
                ('purchase_line_id', '=', False), ('to_refund', '=', True)

            ]
            out_moves = record.env['stock.move'].search(out_domain)
            out_return_moves = record.env['stock.move'].search(out_return_domain)

            out_qtys = sum([m.product_qty for m in out_moves]) - sum([m.product_qty for m in out_return_moves])

            # Earlier Purchase Moves / Adj In
            earlier_moves = self.env['stock.move'].search([
                ('product_id', '=', record.product_id.id),
                ('state', '=', 'done'),
                ('date', '<', record.date),
                ('to_refund', '=', False),
                ('location_dest_id', '=', record.location_id.id)
            ])

            earlier_purchased_qtys = sum(
                [m.purchase_line_id.qty_received if m.purchase_line_id else m.product_qty for m in earlier_moves])
            print('earlier_purchased_qtys', record, earlier_purchased_qtys)
            qtys = record.purchase_line_id.qty_received if record.purchase_line_id else record.product_qty
            print('qtys', record, qtys)
            # If you wanna show Multi Uom Onhand qty as negative value, use this
            # max([report.qtys - (report.out_qtys - earlier_purchased_qtys), 0  if len(later_moves) != 0 else report.qtys - (report.out_qtys - earlier_purchased_qtys)])
            remaining_qtys = max([qtys - (out_qtys - earlier_purchased_qtys),
                                  0]) if not earlier_purchased_qtys >= out_qtys else qtys
            print('remaining_qtys', record, remaining_qtys)
            multi_uom_remaining_qtys = self.convert_to_multi_uom(record.product_id, remaining_qtys)
            print('multi_uom_remaining_qtys', record, multi_uom_remaining_qtys)
            record.write({
                'out_qtys': out_qtys,
                'remaining_qtys': remaining_qtys,
                'multi_uom_remaining_qtys': multi_uom_remaining_qtys
            })

    # Method from multi_uom_module
    def convert_to_multi_uom(self, product, qty_in_pcs):
        total_consumed_qty = 0
        multi_uom_qty = ''
        multi_uom_onhand_qty = False
        if product.multi_uom_ok and product.multi_uom_line_ids:
            lines = product.multi_uom_line_ids
            lines = sorted(lines, key=lambda l: l.ratio, reverse=True)
            remaining_qty = qty_in_pcs
            for line in lines:
                if total_consumed_qty == qty_in_pcs:
                    break

                converted_qty = remaining_qty / line.ratio
                if abs(converted_qty) >= 1:
                    multi_uom_qty += f' {int(converted_qty)} {line.uom_id.name} '
                    consumed_qty = int(converted_qty) * line.ratio
                    remaining_qty -= consumed_qty
                    total_consumed_qty += consumed_qty

        else:
            multi_uom_qty = f'{qty_in_pcs} {product.uom_id.name}'

        return multi_uom_qty if multi_uom_qty else f'{qty_in_pcs} {product.uom_id.name}'

    @api.model
    def create(self, values):
        state = values.get('state', 'draft')
        if state and state == 'done':
            values['out_qtys'], values['remaining_qtys'], values[
                'multi_uom_remaining_qtys'] = self.update_out_and_remaining_qtys()

        print('values', state, values)
        return super(StockMove, self).create(values)

    def write(self, values):
        state = values.get('state', 'draft')
        if state and state == 'done':
            self.update_out_and_remaining_qtys()

        print('write values', state, values, self)
        return super(StockMove, self).write(values)

    @api.model
    def search(self, args, offset=0, limit=None, order=None, count=False):
        res = super(StockMove, self).search(args, offset=0, limit=None, order=None, count=False)
        return res.filtered(lambda l: l.onhand_qtys_in_pcs > 0)
