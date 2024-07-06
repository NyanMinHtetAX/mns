from odoo import models, fields


class AccountMove(models.Model):

    _inherit = 'account.move'

    van_order_id = fields.Many2one('van.order', 'Van Order')


    def _reverse_moves_fieldsales(self, default_values_list=None, cancel=False):
        ''' Reverse a recordset of account.move.
        If cancel parameter is true, the reconcilable or liquidity lines
        of each original move will be reconciled with its reverse's.

        :param default_values_list: A list of default values to consider per move.
                                    ('type' & 'reversed_entry_id' are computed in the method).
        :return:                    An account.move recordset, reverse of the current self.
        '''
        if not default_values_list:
            default_values_list = [{} for move in self]

        if cancel:
            lines = self.mapped('line_ids')
            # Avoid maximum recursion depth.
            if lines:
                lines.remove_move_reconcile()

        reverse_type_map = {
            'entry': 'entry',
            'out_invoice': 'out_refund',
            'out_refund': 'entry',
            'in_invoice': 'in_refund',
            'in_refund': 'entry',
            'out_receipt': 'entry',
            'in_receipt': 'entry',
        }

        move_vals_list = []
        for move, default_values in zip(self, default_values_list):
            default_values.update({
                'move_type': reverse_type_map[move.move_type],
                'reversed_entry_id': move.id,
            })
            move_vals_list.append(move.with_context(move_reverse_cancel=cancel)._reverse_move_vals(default_values, cancel=cancel))
        
        reverse_moves = self.env['account.move'].create(move_vals_list)
        sale_return_data = self.env['sale.stock.return'].sudo().search([('daily_sale_summary_id','=',self.van_order_id.daily_sale_summary_id.id)])
        if sale_return_data:
            for return_data in sale_return_data:
                order_lines = []
                for line in return_data.line_ids:
                    order_lines.append(
                        (0, 0, line.prepare_invoice_line())
                    )
        
        reverse_moves['invoice_line_ids'] = [(5,)]
        reverse_moves['invoice_line_ids'] = order_lines
        for move, reverse_move in zip(self, reverse_moves.with_context(check_move_validity=False, move_reverse_cancel=cancel)):
            # Update amount_currency if the date has changed.
            if move.date != reverse_move.date:
                for line in reverse_move.line_ids:
                    if line.currency_id:
                        line._onchange_currency()
            reverse_move._recompute_dynamic_lines(recompute_all_taxes=False)
        reverse_moves._check_balanced()

        # Reconcile moves together to cancel the previous one.
        if cancel:
            reverse_moves.with_context(move_reverse_cancel=cancel)._post(soft=False)
            for move, reverse_move in zip(self, reverse_moves):
                group = defaultdict(list)
                for line in (move.line_ids + reverse_move.line_ids).filtered(lambda l: not l.reconciled):
                    group[(line.account_id, line.currency_id)].append(line.id)
                for (account, dummy), line_ids in group.items():
                    if account.reconcile or account.internal_type == 'liquidity':
                        self.env['account.move.line'].browse(line_ids).with_context(move_reverse_cancel=cancel).reconcile()

        return reverse_moves

class AccountMoveLine(models.Model):

    _inherit = 'account.move.line'

    van_order_line_id = fields.Many2one('van.order.line', 'Van Order Line')
