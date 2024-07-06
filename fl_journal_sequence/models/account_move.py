# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError


class AccountMove(models.Model):
    _inherit = 'account.move'

    is_sequence_generated = fields.Boolean(string='Sequence Generated', copy=False)

    @api.depends('posted_before', 'state', 'journal_id', 'date')
    def _compute_name(self):
        for move in self:
            if not move.journal_id.sequence_id:
                return super(AccountMove, self)._compute_name()
            sequence = move._get_sequence()
            if not sequence:
                raise UserError(_('Please define a sequence on your journal.'))
            if not move.is_sequence_generated and move.state == 'draft':
                move.name = '/'
            elif not move.is_sequence_generated and move.state != 'draft':
                move.name = sequence.next_by_id()
                move.is_sequence_generated = True

    def _get_sequence(self):
        ''' Return the sequence to be used during the post of the current move.
        :return: An ir.sequence record or False.
        '''
        self.ensure_one()

        journal = self.journal_id
        if self.move_type in ('entry', 'out_invoice', 'in_invoice', 'out_receipt', 'in_receipt') or not journal.refund_sequence:
            return journal.sequence_id
        if not journal.refund_sequence_id:
            return
        return journal.refund_sequence_id
