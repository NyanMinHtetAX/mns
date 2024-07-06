from odoo import models, fields, api, _


class FleetVehicleLogServices(models.Model):
    _inherit = 'fleet.vehicle.log.services'

    expense_service_count = fields.Integer(compute='_compute_service_number', string='Service Count Number')

    expense_product_id = fields.Many2one('product.product', string='Product')
    employee_id = fields.Many2one('hr.employee', string='Employee')
    is_create_done = fields.Boolean(string='Is Converted to Requisition', default=False, copy=False)

    def action_convert_expense(self):
        active_ids = self.env.context.get('active_ids', [])
        lines = self.env['fleet.vehicle.log.services'].browse(active_ids)
        for rec in lines:
            if not rec.is_create_done:
                self.env['hr.expense'].create({
                    'name': rec.description,
                    'total_amount': rec.amount,
                    'unit_amount':rec.amount,
                    'date': rec.date,
                    'product_id': rec.expense_product_id.id,
                    'employee_id': rec.employee_id.id,
                    'fleet_service_log_id': rec.id,
                    'account_id': rec.expense_product_id.property_account_expense_id.id,
                })
            rec.is_create_done = True
        return {
            'effect': {
                'fadeout': 'slow',
                'message': 'Converted To Expense',
                'type': 'rainbow_man',
            }
        }

    def _compute_service_number(self):
        for rec in self:
            service_line = self.env['hr.expense'].search([('fleet_service_log_id', '=', self.id)])
            rec.expense_service_count = len(service_line)

    def action_open_service_expense(self):
        return {
            'type': 'ir.actions.act_window',
            'name': ('All My Expenses'),
            'res_model': 'hr.expense',
            'view_mode': 'tree,form,kanban,graph,pivot',
            'domain': [('fleet_service_log_id', '=', self.id)],
            'context': {}
        }
