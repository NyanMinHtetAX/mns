from odoo import fields, models, api


class AccountMove(models.Model):
    _inherit = 'stock.picking'

    report_template_id = fields.Many2one('custom.report.template', string="Report Template", required=False)
