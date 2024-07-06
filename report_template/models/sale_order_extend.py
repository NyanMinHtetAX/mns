# -*- coding: utf-8 -*-

from odoo import fields, models, api


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    report_template_id = fields.Many2one('custom.report.template', string="Report Template", required=False)

    @api.onchange('branch_id')
    def onchange_template_id(self):
        for rec in self:
            templates = self.env['custom.report.template'].search([('report_branch_id', '=', rec.branch_id.id)])
            if templates:
                rec.report_template_id = templates[-1].id

    @api.model
    def _prepare_picking(self):

        res = super(SaleOrder, self)._prepare_picking()
        res.update({
            'is_sale_order': True,
        })
        return res

    def _prepare_invoice(self):
        res = super(SaleOrder, self)._prepare_invoice()
        res.update({
            'is_sale_order': True,
        })
        return res
