import json

from odoo import fields, api, models, _
from xml.dom import minidom


class DynamicButton(models.Model):
    _name = 'dynamic.button'
    _description = 'Dynamic Button'
    _rec_name = 'verbose_name'

    name = fields.Char(required=True, copy=False)
    technical_name = fields.Char()
    model = fields.Char()
    view = fields.Char()
    verbose_name = fields.Char(compute='compute_verbose_name', store=True)

    @api.depends('name', 'view')
    def compute_verbose_name(self):
        for button in self:
            button.verbose_name = f'{button.name} ({button.view})'


class DynamicPage(models.Model):
    _name = 'dynamic.page'
    _description = 'Dynamic Page'
    _rec_name = 'verbose_name'

    name = fields.Char(required=True, copy=False)
    model = fields.Char()
    view = fields.Char()
    verbose_name = fields.Char(compute='compute_verbose_name', store=True)

    @api.depends('name', 'view')
    def compute_verbose_name(self):
        for page in self:
            page.verbose_name = f'{page.name} ({page.view})'


class ButtonRule(models.Model):
    _name = 'dynamic.button_rule'
    _description = 'Dynamic Button Rule'

    config_id = fields.Many2one('dynamic.access.config', required=True, ondelete='cascade')
    name = fields.Char(compute="compute_rule_name")
    button = fields.Many2many('dynamic.button', 'button', 'col1', 'col2', ondelete='cascade', required=True)
    restriction = fields.Selection([('disabled', 'Disabled'), ('hidden', 'Hidden')], required=True)
    button_domain = fields.Char(compute='compute_button_domain', store=True)

    @api.depends('config_id')
    def compute_button_domain(self):
        for line in self:
            dmn = json.dumps([('model', '=', line.config_id.model_name),
                              ('view', 'in', [view.name for view in line.config_id.view])])
            line.button_domain = dmn

    def compute_rule_name(self):
        for rule in self:
            rule.name = ''.join([f'({button.name})-{rule.restriction}' for button in rule.button])


class PageRule(models.Model):
    _name = 'dynamic.page_rule'
    _description = 'Dynamic Page Rule'

    config_id = fields.Many2one('dynamic.access.config', required=True, ondelete='cascade')
    name = fields.Char(compute="compute_rule_name")
    page = fields.Many2many('dynamic.page', ondelete='cascade', required=True)
    restriction = fields.Selection([('hidden', 'Hidden')], default='hidden', required=True)
    page_domain = fields.Char(compute='compute_page_domain', store=True)

    @api.depends('config_id')
    def compute_page_domain(self):
        for line in self:
            model_names = line.config_id.model.inherited_model_ids.mapped('model') + [line.config_id.model_name]
            views = self.env['ir.ui.view'].sudo().search([('model', 'in', model_names)])
            print("views", views.mapped('name'))
            dmn = json.dumps([('view', 'in', views.mapped('name'))])
            line.page_domain = dmn

    def compute_rule_name(self):
        for rule in self:
            rule.name = ''.join([f'({page.name})-{rule.restriction}' for page in rule.page])


class DynamicAccessConfig(models.Model):
    _name = 'dynamic.access.config'
    _description = 'Dynamic Access'

    model = fields.Many2one('ir.model')
    view = fields.Many2many('ir.ui.view', required=True)
    model_name = fields.Char(related='model.model')
    users = fields.Many2many('res.users')
    groups = fields.Many2many('res.groups')
    appy_to = fields.Selection([('selected', 'Only selected users & groups'), ('all', 'Everyone else')],
                               default='selected', required=True)
    button_rules = fields.One2many('dynamic.button_rule', 'config_id', string="Buttons")
    page_rules = fields.One2many('dynamic.page_rule', 'config_id', string="Pages")

    def applies_to_current_user(self):
        self.ensure_one()
        user = self.env.user
        is_selected = (self.users and user in self.users) or (
                self.groups and any((user in group.users) for group in self.groups))
        return (self.appy_to == 'selected' and is_selected) or (self.appy_to == 'all' and not is_selected)

    @api.onchange('model')
    def onchange_model(self):
        res = {'value': {'view': False}, 'domain': {'view': [('id', '=', -1)]}}
        if self.model:
            res.update({'domain': {'view': [('model', '=', self.model.model)]}})
        return res

    @api.onchange('model')
    def onchange_view(self):
        model_names = self.model.inherited_model_ids.mapped('model') + [self.model_name]
        views = self.env['ir.ui.view'].sudo().search([('model', 'in', model_names)])
        if views:
            print("views", views)
            views.discover_buttons_and_pages()


class IRUIView(models.Model):
    _inherit = 'ir.ui.view'

    def discover_buttons_and_pages(self):
        env = self.env['ir.ui.view'].sudo()
        views = self or env.browse(self._context.get('active_ids', [])) or env.search([])
        for view in views:
            dom = minidom.parseString(view.arch)
            buttons = dom.getElementsByTagName('button')
            pages = dom.getElementsByTagName('page')
            tree_default_buttons = {'Create': 'o_list_button_add', 'Import': 'o_button_import',
                                    'Export': 'o_list_export_xlsx', 'Filters': 'o_search_options',
                                    'Print & Action': 'o_cp_action_menus', 'View switcher': 'o_cp_switch_buttons'}
            kanban_default_buttons = {'Create': 'o-kanban-button-new', 'Import': 'o_button_import',
                                      'Filters': 'o_search_options', 'View switcher': 'o_cp_switch_buttons'}
            form_default_buttons = {'Create': 'o_form_button_create', 'Edit': 'o_form_button_edit',
                                    'Print & Action': 'o_cp_action_menus'}
            default_buttons = {}
            if 'tree' in view.name:
                default_buttons = tree_default_buttons
            elif 'form' in view.name:
                default_buttons = form_default_buttons
            elif 'kanban' in view.name:
                default_buttons = kanban_default_buttons
            for key, value in default_buttons.items():
                if not self.env['dynamic.button'].search_count(
                        [('name', '=', key), ('model', '=', view.model), ('view', '=', view.name)]):
                    data = {
                        "name": key,
                        "model": view.model,
                        "view": view.name,
                        "technical_name": value,
                    }
                    self.env['dynamic.button'].sudo().create([data])
                q = self.env['dynamic.button'].sudo().search(
                    [('name', '=', key), ('model', '=', view.model), ('view', '=', view.name)])
                q.update({'technical_name': value})

            for button in buttons:
                name = button.getAttribute('string') or button.getAttribute('name')
                contained_field = button.getElementsByTagName("field")
                if contained_field:
                    name = contained_field[0].getAttribute("string") or name
                spans = button.getElementsByTagName("span")
                for span in spans:
                    if span.getAttribute("class") == "o_stat_text":
                        name = span.firstChild.data
                        break
                if not self.env['dynamic.button'].search_count(
                        [('name', '=', name), ('model', '=', view.model), ('view', '=', view.name)]):
                    data = {
                        "name": name,
                        "model": view.model,
                        "view": view.name,
                        "technical_name": button.getAttribute('name'),
                    }
                    self.env['dynamic.button'].sudo().create([data])

                q = self.env['dynamic.button'].sudo().search(
                    [('name', '=', name), ('model', '=', view.model), ('view', '=', view.name)])
                q.update({'technical_name': button.getAttribute('name')})

            for page in pages:
                name = page.getAttribute('string') or page.getAttribute('name')
                if name == 'Invoicing' and view.name == "res.partner.property.form.inherit":
                    name = "Accounting"
                if not self.env['dynamic.page'].search_count(
                        [('name', '=', name), ('model', '=', view.model), ('view', '=', view.name)]):
                    data = {
                        "name": name,
                        "model": view.model,
                        "view": view.name,
                    }
                    self.env['dynamic.page'].sudo().sudo().create([data])


class GroupAssignment(models.Model):
    _name = 'res.groups.assign'
    _inherit = ['mail.thread']
    _description = 'Batch Group Assignment'

    users = fields.Many2many('res.users', required=True, domain=lambda self: [('id', '!=', self.env.user.id)])
    operation_type = fields.Selection([('add', 'Add'), ('remove', 'Remove')], required=True, default='add')
    groups = fields.Many2many('res.groups', required=True,
                              domain=lambda self: [('category_id.name', 'not ilike', 'User Types')])
    target_users = fields.Selection([('selected', 'Only selected users'), ('all', 'Everyone else')], required=True,
                                    default='selected')
    target_groups = fields.Selection([('selected', 'Only selected groups'), ('all', 'All others')], required=True,
                                     default='selected')

    @api.model
    def execute_assignment(self):
        try:
            self.ensure_one()
            ids = [user.id for user in self.users]
            groups = self.groups
            if self.target_groups == 'all':
                groups = self.env['res.groups'].search([('category_id.name', 'not ilike', 'User Types')]).filtered(
                    lambda grp: grp not in self.groups)
            if self.target_users == 'all':
                ids = self.env['res.users'].search([]).filtered(lambda user: user not in self.users).mapped('id')
            if self.operation_type == 'add':
                for group in self.groups:
                    group.users = list(set([(4, user.id) for user in group.users] + [(4, uid) for uid in ids]))
            else:
                for group in groups:
                    group.users = [(6, 0, [user.id for user in group.users if user.id not in ids])]

            msg = 'Operation Completed Successfully'
            wizard = self.env['dynamic.feedback.wizard'].create({'message': msg})
            return {
                'name': _('Success'),
                'type': 'ir.actions.act_window',
                'view_mode': 'form',
                'res_model': 'dynamic.feedback.wizard',
                'res_id': wizard.id,
                'target': 'new',
            }

        except Exception as e:
            msg = 'Something went wrong!'
            wizard = self.env['dynamic.feedback.wizard'].create([{'message': e or msg}])
            return {
                'name': _('Operation Failed!'),
                'type': 'ir.actions.act_window',
                'view_mode': 'form',
                'res_model': 'dynamic.feedback.wizard',
                'res_id': wizard.id,
                'target': 'new',
                'context': {'active_id': self.id}
            }
