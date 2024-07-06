from odoo import fields, models, api


class AccountMove(models.Model):
    _inherit = 'account.move'

    report_template_id = fields.Many2one('custom.report.template', string="Report Template", required=False)

    # @api.onchange('branch_id')
    # def onchange_template_id(self):
    #     for rec in self:
    #         templates = self.env['custom.report.template'].search([('report_branch_id', '=', rec.branch_id.id)])
    #         if templates:
    #             rec.report_template_id = templates[-1].id


class AccountPayment(models.Model):
    _inherit ='account.payment'

    report_template_id = fields.Many2one('custom.report.template', string="Report Template", required=False)