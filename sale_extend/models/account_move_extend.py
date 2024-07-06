from odoo import models, fields, api, _


class AccountMove(models.Model):
    _inherit = 'account.move'

    total_amount = fields.Monetary(string='Total Amount', compute='_compute_total_amount', )
    total_due = fields.Monetary('Total Due Amount', compute='compute_total_due', readonly=True
                                )
    partner_class_id = fields.Many2one('partner.class', related='partner_id.partner_class_id', readonly=True)

    fleet_id = fields.Many2one('fleet.vehicle', string='Car Model')
    license_plate = fields.Char(string='License Plate', related='fleet_id.license_plate')
    payment_type = fields.Selection(string='Payment Type', related='partner_id.payment_type')
    is_sale_order = fields.Boolean(string='Is Sale Order', default=False)
    foc_amount = fields.Char("FOC Amount")
    city_id = fields.Many2one('res.city', string='Cities', related='partner_id.x_city_id', store=True)

    @api.depends('amount_residual', 'total_due')
    def _compute_total_amount(self):
        for rec in self:
            rec.total_amount = 0
            if rec.amount_residual or rec.total_due:
                if rec.move_type == 'out_invoice' or rec.move_type == 'in_invoice':
                    rec.total_amount = rec.amount_residual + abs(rec.total_due)
                if rec.move_type == 'out_refund' or rec.move_type == 'in_refund':
                    rec.total_amount = abs(rec.total_due) - rec.amount_residual


    @api.depends('partner_id')
    def compute_total_due(self):
        invoices = []
        invoices_credit = []
        for rec in self:
            rec.total_due = 0.0

            if rec.partner_id and rec.id and rec.partner_id.customer and not rec.partner_id.supplier:
                invoices = self.env['account.move'].search([('id', '<', rec.id),
                                                            ('partner_id', '=', rec.partner_id.id),
                                                            ('state', '=', 'posted'),
                                                            ('id', '!=', rec.id),
                                                            ('move_type', '=', 'out_invoice')
                                                            ])
                credits = self.env['account.move'].search([
                                                            ('partner_id', '=', rec.partner_id.id),
                                                            ('state', '=', 'posted'),
                                                            ('id', '!=', rec.id),
                                                            ('move_type', '=', 'out_refund')
                                                            ])
                if invoices:
                    for inv in invoices:
                        rec.total_due += inv.amount_residual
                if credits:
                    for cre in credits:
                        rec.total_due -= cre.amount_residual
            if rec.partner_id and rec.id and rec.partner_id.supplier and not rec.partner_id.customer:
                invoices = self.env['account.move'].search([('id', '<', rec.id),
                                                            ('partner_id', '=', rec.partner_id.id),
                                                            ('state', '=', 'posted'),
                                                            ('id', '!=', rec.id),
                                                            ('move_type', '=', 'in_invoice')
                                                            ])
                credits = self.env['account.move'].search([
                                                            ('partner_id', '=', rec.partner_id.id),
                                                            ('state', '=', 'posted'),
                                                            ('id', '!=', rec.id),
                                                            ('move_type', '=', 'in_refund')
                                                            ])
                if invoices:
                    for inv in invoices:
                        rec.total_due += inv.amount_residual
                if credits:
                    for cre in credits:
                        rec.total_due -= cre.amount_residual
