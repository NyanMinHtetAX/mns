from odoo import models, fields, api, _


class HrExpense(models.Model):
    _inherit = 'hr.expense'

    def _get_default_expense_sheet_values(self):
        res = super(HrExpense, self)._get_default_expense_sheet_values()

        if self.analytic_account_id:
            res.update({
                'default_analytic_account_id':self.analytic_account_id.id
            })
        return res


class HrExpenseSheet(models.Model):
    _inherit = ['hr.expense.sheet']

    product_id = fields.Many2one('product.product', related='expense_line_ids.product_id', string="Product", store=True)

    analytic_account_id = fields.Many2one('account.analytic.account', 'Analytic Account')
    category = fields.Many2one('product.category', string='Category',compute='_compute_categ_id', store=True,groups="base.group_user")

    @api.depends('product_id')
    def _compute_categ_id(self):
        for record in self:
            record.category = record.product_id.categ_id.id if record.product_id else False

    def action_register_payment(self):
        samples = self.mapped('expense_line_ids.sample')
        if samples.count(True):
            action = self.env['ir.actions.actions']._for_xml_id('hr_expense_extract.action_expense_sample_register')
            action['context'] = {'active_id': self.id}
            return action

        return super().action_register_payment()
