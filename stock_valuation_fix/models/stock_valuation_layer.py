from odoo import api, models, fields, _
from odoo.exceptions import UserError
import re


class StockValuationLayer(models.Model):

    _inherit = 'stock.valuation.layer'

    def write(self, values):
        for svl in self:
            if self.env.context.get('from_view', False):
                if values.get('unit_cost') or values.get('unit_cost') == 0.00:
                    description = f'Changed Unit Cost from {svl.unit_cost} to {values["unit_cost"]}'
                    self.env['svl.fix.history'].create({
                        'name': description,
                        'svl_id': svl.id,
                        'user_id': self.env.user.id,
                    })
                    values['value'] = values['unit_cost'] * svl.quantity
                elif values.get('quantity') or values.get('quantity') == 0:
                    description = f'Changed Quantity from {svl.quantity} to {values["quantity"]}'
                    self.env['svl.fix.history'].create({
                        'name': description,
                        'svl_id': svl.id,
                        'user_id': self.env.user.id,
                    })
                    values['value'] = values['quantity'] * svl.unit_cost
            return super().write(values)

    def _delete_stock_journal(self):
        for svl in self:
            if not svl.account_move_id:
                continue
            balance = svl.account_move_id.line_ids.mapped('balance')
            if len(balance) >= 1:
                description = f'Deleted Stock Journal With Value -  {abs(balance[0])}\n' \
                              f'Ref - {svl.account_move_id.ref}\n' \
                              f'Sequence - {svl.account_move_id.name}'
                self.env['svl.fix.history'].create({
                    'name': description,
                    'svl_id': svl.id,
                    'user_id': self.env.user.id,
                })
            svl.account_move_id.with_context(force_delete=True).sudo().unlink()

    def _generate_stock_journal(self):
        am_vals = []
        for svl in self:
            if svl.account_move_id:
                raise UserError('Please delete the existing stock journal first. '
                                'And make sure to change the cost before re-generating stock jouranl.')
            description = f'Generated Stock Journal With Value -  {svl.value}\n' \
                          f'Unit Cost - {svl.unit_cost}\n'
            self.env['svl.fix.history'].create({
                'name': description,
                'svl_id': svl.id,
                'user_id': self.env.user.id,
            })
            accounting_date = fields.Datetime.context_timestamp(svl, svl.date)
            if svl.stock_move_id:
                am_vals += svl.stock_move_id.with_context(force_period_date=accounting_date)._account_entry_move(svl.quantity, svl.description, svl.id, svl.value)
            else:
                product_accounts = {product.id: product.product_tmpl_id.get_product_accounts() for product in svl.product_id}
                am_vals_list = []
                pattern = r'\(([^)]+)\)'
                match = re.search(pattern, svl.description)
                if match:
                    # Extract the text within parentheses
                    name = match.group(1)
                else:
                    raise UserError('You have no Stock Move or Not be cost update')

                product = svl.product_id
                value = svl.value

                if product.type != 'product' or product.valuation != 'real_time':
                    continue

                # Sanity check.
                # if not product_accounts[product.id].get('expense'):
                #     raise UserError(_('You must set a counterpart account on your product category.'))
                # if not product_accounts[product.id].get('stock_valuation'):
                #     raise UserError(
                #         _('You don\'t have any stock valuation account defined on your product category. You must define one before processing this operation.'))

                if value < 0:
                    debit_account_id = product_accounts[product.id]['expense'].id
                    credit_account_id = product_accounts[product.id]['stock_valuation'].id
                else:
                    debit_account_id = product_accounts[product.id]['stock_valuation'].id
                    credit_account_id = product_accounts[product.id]['expense'].id

                move_vals = {
                    'journal_id': product_accounts[product.id]['stock_journal'].id,
                    'company_id': svl.company_id.id,
                    'ref': product.default_code,
                    'stock_valuation_layer_ids': [(6, None, [svl.id])],
                    'move_type': 'entry',
                    'line_ids': [(0, 0, {
                        'name': _(
                            '%(user)s changed cost %(name)s - %(product)s',
                            user=self.create_uid.id,
                            name = name,
                            product=product.display_name
                        ),
                        'account_id': debit_account_id,
                        'debit': abs(value),
                        'credit': 0,
                        'product_id': product.id,
                    }), (0, 0, {
                        'name': _(
                            '%(user)s changed cost %(name)s - %(product)s',
                            user=self.env.user.name,
                            name=name,
                            product=product.display_name
                        ),
                        'account_id': credit_account_id,
                        'debit': 0,
                        'credit': abs(value),
                        'product_id': product.id,
                    })],
                }
                am_vals.append(move_vals)
            if am_vals:
                account_moves = self.env['account.move'].sudo().create(am_vals)
                account_moves._post()


class SvlFixHistory(models.Model):

    _name = 'svl.fix.history'
    _description = 'SVL fixed History'

    name = fields.Text('Description')
    user_id = fields.Many2one('res.users', 'Users')
    svl_id = fields.Many2one('stock.valuation.layer', 'Valuation')
    product_id = fields.Many2one('product.product', 'Product', related='svl_id.product_id', store=True)
