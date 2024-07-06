from odoo import api, models, fields
from odoo.exceptions import UserError


class AccountMove(models.Model):

    _inherit = 'account.move'

    invoice_address_id = fields.Many2one('res.partner',string='Invoice Address',domain=[('type', '=', "invoice")]) 
    
    def assign_to_cash_collector(self):
        ctx = dict(self.env.context)
        invoices = self.filtered_domain([('state', '=', 'posted'),
                                         ('move_type', '=', 'out_invoice'),
                                         ('payment_state', 'in', ['not_paid', 'partial']),
                                         ('amount_residual', '!=', 0)])
        if not invoices:
            raise UserError('Please select an invoice which is not paid yet.')
        ctx['default_invoice_ids'] = invoices.ids
        return {
            'name': 'Assign Cash Collector',
            'type': 'ir.actions.act_window',
            'res_model': 'assign.to.cash.collector',
            'view_mode': 'form',
            'target': 'new',
            'context': ctx,
        }

    @api.model
    def fields_view_get(self, view_id=None, view_type='form', toolbar=False, submenu=False):
        res = super(AccountMove, self).fields_view_get(view_id=view_id,
                                                       view_type=view_type,
                                                       toolbar=toolbar,
                                                       submenu=submenu)
        assign_to_collector_action_id = self.env.ref('fs_payment_collection.action_assign_to_cash_collector').id
        actions = res.get('toolbar', {}).get('action', [])
        for action in actions:
            if action['id'] != assign_to_collector_action_id:
                continue
            if not self.env.context.get('default_move_type') == 'out_invoice':
                res['toolbar']['action'].remove(action)
        return res
