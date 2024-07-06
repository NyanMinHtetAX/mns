# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class AccountJournal(models.Model):
    _inherit = 'account.journal'

    sequence_id = fields.Many2one('ir.sequence', string='Entry Sequence', copy=False,
                                  help="This field contains the information related to the numbering of the journal entries of this journal.")
    refund_sequence_id = fields.Many2one('ir.sequence', string='Credit Note Entry Sequence', copy=False,
                                         help="This field contains the information related to the numbering of the credit note entries of this journal.")
    sequence_number_next = fields.Integer(string='Next Number', compute='_compute_seq_number_next', inverse='_inverse_seq_number_next',
                                          help='The next sequence number will be used for the next invoice.')
    refund_sequence_number_next = fields.Integer(string='Credit Notes Next Number', compute='_compute_refund_seq_number_next',
                                                 inverse='_inverse_refund_seq_number_next',
                                                 help='The next sequence number will be used for the next credit note.')

    # do not depend on 'sequence_id.date_range_ids', because
    # sequence_id._get_current_sequence() may invalidate it!
    @api.depends('sequence_id.use_date_range', 'sequence_id.number_next_actual')
    def _compute_seq_number_next(self):
        '''Compute 'sequence_number_next' according to the current sequence in use,
        an ir.sequence or an ir.sequence.date_range.
        '''
        for journal in self:
            if journal.sequence_id:
                sequence = journal.sequence_id._get_current_sequence()
                journal.sequence_number_next = sequence.number_next_actual
            else:
                journal.sequence_number_next = 1

    def _inverse_seq_number_next(self):
        '''Inverse 'sequence_number_next' to edit the current sequence next number.
        '''
        for journal in self:
            if journal.sequence_id and journal.sequence_number_next:
                sequence = journal.sequence_id._get_current_sequence()
                sequence.sudo().number_next = journal.sequence_number_next

    # do not depend on 'refund_sequence_id.date_range_ids', because
    # refund_sequence_id._get_current_sequence() may invalidate it!
    @api.depends('refund_sequence_id.use_date_range', 'refund_sequence_id.number_next_actual')
    def _compute_refund_seq_number_next(self):
        '''Compute 'sequence_number_next' according to the current sequence in use,
        an ir.sequence or an ir.sequence.date_range.
        '''
        for journal in self:
            if journal.refund_sequence_id and journal.refund_sequence:
                sequence = journal.refund_sequence_id._get_current_sequence()
                journal.refund_sequence_number_next = sequence.number_next_actual
            else:
                journal.refund_sequence_number_next = 1

    def _inverse_refund_seq_number_next(self):
        '''Inverse 'refund_sequence_number_next' to edit the current sequence next number.
        '''
        for journal in self:
            if journal.refund_sequence_id and journal.refund_sequence and journal.refund_sequence_number_next:
                sequence = journal.refund_sequence_id._get_current_sequence()
                sequence.sudo().number_next = journal.refund_sequence_number_next

    @api.model
    def _get_sequence_prefix(self, code, refund=False):
        prefix = code.upper()
        if refund:
            prefix = 'R' + prefix
        return prefix + '/%(range_year)s/'

    @api.model
    def create_sequence(self, refund=False):
        """ Create new no_gap entry sequence for every new Journal"""
        prefix = self._get_sequence_prefix(self.code, refund)
        seq_name = refund and self.code + _(': Refund') or self.code
        seq = {
            'name': _('%s Sequence') % seq_name,
            'implementation': 'no_gap',
            'prefix': prefix,
            'padding': 4,
            'number_increment': 1,
            'use_date_range': True,
        }
        if self.company_id:
            seq['company_id'] = self.company_id.id
        seq = self.env['ir.sequence'].create(seq)
        seq_date_range = seq._get_current_sequence()
        seq_date_range.number_next = refund and (self.refund_sequence_number_next or 1) or (self.sequence_number_next or 1)
        return seq

    def create_journal_sequence(self):
        if not self.sequence_id:
            sequence = self.create_sequence(refund=False)
            self.sequence_id = sequence.id
        if not self.refund_sequence_id:
            refund_sequence = self.create_sequence(refund=True)
            self.refund_sequence_id = refund_sequence.id
