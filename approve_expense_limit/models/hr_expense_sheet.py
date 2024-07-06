from odoo import api, models, fields, _


class HrExpenseSheet(models.Model):
    _inherit = 'hr.expense.sheet'

    is_approve = fields.Boolean('Get Approve', compute='check_get_approve')
    limit_user_ids = fields.Many2many('res.users', string='Limit Users', store=True,
                                      compute='_get_limit_user_id')

    @api.depends('total_amount')
    def check_get_approve(self):
        for rec in self:
            user = self.env.user
            group_id = self.env.ref('hr_expense.group_hr_expense_manager')
            if rec.can_approve and rec.state == 'submit':
                if user and user.is_limit_expense and user.limit_expense_amount and rec.total_amount and rec.total_amount <= user.limit_expense_amount:
                    rec.is_approve = True
                elif user and not user.is_limit_expense and group_id in user.groups_id:
                    rec.is_approve = True
                else:
                    rec.is_approve = False
            else:
                rec.is_approve = False

    @api.depends('total_amount')
    def _get_limit_user_id(self):
        for sheet in self:
            limit_users = sheet.env['res.users'].search([('is_limit_expense', '=', True)])
            no_limit_users = sheet.env['res.users'].search([('is_limit_expense', '=', False)])
            f_limit_users = []
            if limit_users:
                for l_user in limit_users:
                    if sheet.total_amount <= l_user.limit_expense_amount:
                        f_limit_users.append(l_user.id)
            if no_limit_users:
                for n_l_user in no_limit_users:
                    f_limit_users.append(n_l_user.id)
            sheet.limit_user_ids = f_limit_users



