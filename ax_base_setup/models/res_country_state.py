from odoo import models, fields, api, _


class ResCountryState(models.Model):

    _inherit = "res.country.state"

    customer_sequence_id = fields.Many2one('ir.sequence', string='Customer Sequence', required=False, copy=False)
    supplier_sequence_id = fields.Many2one('ir.sequence', string='Vendor Sequence', required=False, copy=False)
    customer_sequence_number_next = fields.Integer(string='Cust. Next Number',
                                                   compute='_compute_customer_seq_number_next',
                                                   inverse='_set_customer_seq_number_next')
    supplier_sequence_number_next = fields.Integer(string='Vend. Next Number',
                                                   compute='_compute_supplier_seq_number_next',
                                                   inverse='_set_supplier_seq_number_next')

    @api.depends('customer_sequence_id.number_next_actual')
    def _compute_customer_seq_number_next(self):
        for state in self:
            if state.customer_sequence_id:
                sequence = state.customer_sequence_id._get_current_sequence()
                state.customer_sequence_number_next = sequence.number_next_actual
            else:
                state.customer_sequence_number_next = 1

    def _set_customer_seq_number_next(self):
        for state in self:
            if state.customer_sequence_id and state.customer_sequence_number_next:
                sequence = state.customer_sequence_id._get_current_sequence()
                sequence.sudo().number_next = state.customer_sequence_number_next

    @api.depends('supplier_sequence_id.number_next_actual')
    def _compute_supplier_seq_number_next(self):
        for state in self:
            if state.supplier_sequence_id:
                sequence = state.supplier_sequence_id._get_current_sequence()
                state.supplier_sequence_number_next = sequence.number_next_actual
            else:
                state.supplier_sequence_number_next = 1

    def _set_supplier_seq_number_next(self):
        for state in self:
            if state.supplier_sequence_id and state.supplier_sequence_number_next:
                sequence = state.supplier_sequence_id._get_current_sequence()
                sequence.sudo().number_next = state.supplier_sequence_number_next

    @api.model
    def _get_sequence_prefix(self, code):
        prefix = code.upper()
        return prefix

    def _create_customer_sequence(self, vals):
        prefix = self._get_sequence_prefix(vals['code'])
        seq_name = vals['code']
        seq = {
            'name': _('%s Sequence') % seq_name,
            'implementation': 'no_gap',
            'prefix': f'{prefix}%(y)s',
            'padding': 4,
            'number_increment': 1,
            'use_date_range': True,
        }
        seq = self.env['ir.sequence'].create(seq)
        return seq

    def _create_supplier_sequence(self, vals):
        prefix = self._get_sequence_prefix(self._get_sequence_prefix(vals['code']))
        seq_name = vals['code']
        seq = {
            'name': _('%s Sequence') % seq_name,
            'implementation': 'no_gap',
            'prefix': f'V{prefix}%(y)s',
            'padding': 4,
            'number_increment': 1,
            'use_date_range': False,
        }
        seq = self.env['ir.sequence'].create(seq)
        return seq

    @api.model
    def create(self, vals):
        if not vals.get('customer_sequence_id'):
            vals.update({'customer_sequence_id': self.sudo()._create_customer_sequence(vals).id})
            vals.update({'supplier_sequence_id': self.sudo()._create_supplier_sequence(vals).id})
        state = super(ResCountryState, self).create(vals)
        return state
