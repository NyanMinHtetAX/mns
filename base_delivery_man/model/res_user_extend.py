from odoo import models, fields, api, _
from odoo.fields import Command


class Users(models.Model):
    _inherit = 'res.users'

    is_delivery_man = fields.Boolean(string='Delivery Man', default=False)
    is_portal_user = fields.Boolean('Is Portal User',
                                    compute='_compute_is_portal_user',
                                    search='_search_is_portal_user')
    @api.onchange('group_ids')
    def onchange_group(self):
        print('///////')

    @api.model
    def default_get(self, fields_list):
        values = super().default_get(fields_list)
        if self.env.context.get('auto_select_portal'):
            portal_group_id = self.env.ref('base.group_portal').id
            values['groups_id'] = [Command.link(portal_group_id)]
        return values

    def _compute_is_portal_user(self):

        portal_users = self.env.ref('base.group_portal').sudo().users
        non_portal_users = self - portal_users
        portal_users.is_portal_user = True
        non_portal_users.is_portal_user = False

    def _search_is_portal_user(self, operator, value):
        all_users = self.env['res.users'].search([])
        portal_users = self.env.ref('base.group_portal').users
        if operator not in ['=', '!=']:
            raise ValueError(_('This operator is not supported'))
        if (operator == '=' and value) or (operator == '!=' and not value):
            user_ids = portal_users
        else:
            user_ids = all_users - portal_users
        return [('id', 'in', user_ids.ids)]

    @api.model_create_multi
    def create(self, vals_list):
        users = super(Users, self).create(vals_list)
        for user in users:
            # if partner is global we keep it that way
            if user.partner_id.company_id:
                user.partner_id.company_id = user.company_id
            user.partner_id.active = user.active
            user.partner_id.is_delivery_man = user.is_delivery_man
        return users
