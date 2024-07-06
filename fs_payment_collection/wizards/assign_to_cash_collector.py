from odoo import api, models, fields
from itertools import groupby
from odoo.exceptions import UserError


class AssignToCashCollector(models.TransientModel):

    _name = 'assign.to.cash.collector'
    _description = 'Assign To Cash Collector'

    date = fields.Date('Collected Date', default=lambda self: fields.Date.context_today(self), required=1)
    user_id = fields.Many2one('res.users','Collector', domain=[('share', '=', False)], required=1)
    team_id = fields.Many2one('crm.team', 'Sales Team', required=1, domain=[('is_van_team', '=', True)])
    invoice_ids = fields.Many2many('account.move', string='Invoices', required=1)

    @api.onchange('user_id')
    def onchange_user_id(self):
        team_id = self.env['crm.team'].search([]).filtered(lambda team: self.user_id.id in team.member_ids.ids)
        if team_id:
            self.team_id = team_id[0].id

    def btn_assign(self):
        lines = []
        grouped_invoices = groupby(self.invoice_ids, lambda inv: inv.partner_id.id)
        values = (item['invoice_address_id'] for item in self.invoice_ids)
        common_value = next(values, None)
        result =  common_value if all(value == common_value for value in values) else None
        for inv in self.invoice_ids:
            if inv.invoice_address_id:
                if not result:
                    raise UserError('Please assign invoices which have same invoice addresses')
        for partner_id, invoices in grouped_invoices:
            payment_collection = self.env['payment.collection'].search([('to_collect_date', '=', self.date),
                                                                        ('partner_id', '=', partner_id),
                                                                        ('team_id', '=', self.team_id.id)])
            
            for inv in invoices:
                result_tuple = (0, 0, {'invoice_id': inv.id, 'payment_state': inv.payment_state})
                lines.append(result_tuple)
            if not payment_collection:
                payment_collection = self.env['payment.collection'].create({
                    'partner_id': partner_id,
                    'sale_man_id': self.user_id.id,
                    'team_id': self.team_id.id,
                    'to_collect_date': self.date,
                    'invoice_address_id': self.invoice_ids[0].invoice_address_id.id
                })
            else:
                if payment_collection.line_ids:
                    values = (item['invoice_id']['invoice_address_id'] for item in payment_collection.line_ids)
                    common_value = next(values, None)
                    result =  common_value if all(value == common_value for value in values) else None
        
                    for line in payment_collection.line_ids:
                        if line.invoice_id.invoice_address_id:
                            if not result:
                                raise UserError('Please assign invoices which have same invoice addresses')
                        else:
                            raise UserError('Please assign invoices which have same invoice addresses')
            payment_collection.write({'line_ids': lines})
