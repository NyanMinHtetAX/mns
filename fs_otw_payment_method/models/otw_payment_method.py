from odoo import api, fields, models, _
from odoo.exceptions import UserError


class OtwPaymentMethod(models.Model):

    _name = "otw.payment.method"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Payment Methods"
    _order = "id asc"

    name = fields.Char(string="Method", required=True, translate=True, help='Defines the name of the payment method that will be displayed in the Point of Sale when the payments are selected.')
    journal_id = fields.Many2one('account.journal',
                                 string='Journal',
                                 domain=[('type', 'in', ('cash', 'bank'))],
                                 ondelete='restrict',
                                 help='Leave empty to use the receivable account of customer.\n'
                                      'Defines the journal where to book the accumulated payments (or individual payment if Identify Customer is true) after closing the session.\n'
                                      'For cash journal, we directly write to the default account in the journal via statement lines.\n'
                                      'For bank journal, we write to the outstanding account specified in this payment method.\n'
                                      'Only cash and bank journals are allowed.')
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)
    active = fields.Boolean('Active', default=True)
    is_bank = fields.Boolean(string='Bank',default=False,compute='_get_bank_info')

    @api.depends('journal_id')
    def _get_bank_info(self):
        for rec in self:
            rec.is_bank = False
            if rec.journal_id:
                if rec.journal_id.type == 'bank':
                    rec.is_bank = True
                else:
                    rec.is_bank = False


    @api.depends('type')
    def _compute_hide_use_payment_terminal(self):
        no_terminals = not bool(self._fields['use_payment_terminal'].selection(self))
        for payment_method in self:
            payment_method.hide_use_payment_terminal = no_terminals or payment_method.type in ('cash', 'pay_later')
