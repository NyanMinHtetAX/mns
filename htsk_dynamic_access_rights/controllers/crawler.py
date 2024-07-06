from odoo import http
from odoo.http import request
from collections import defaultdict


class DynamicAccess(http.Controller):

    def get_page_values(self, rule):
        return {page.name: rule.restriction for page in rule.page}

    def get_button_values(self, rule):
        return {button.technical_name: rule.restriction for button in rule.button}

    def get_default_value(self):
        return {'buttons': {}, 'pages': {}}

    @http.route(['/fetch-dynamic-objects'], type="json", auth="user", website=False, methods=['POST'],
                csrf=False)
    def fetch_dynamic_objects(self):
        data = defaultdict(self.get_default_value)
        user_restrictions = request.env['dynamic.access.config'].sudo().search([]).filtered(
            lambda config: config.applies_to_current_user())
        for restriction in user_restrictions:
            page_rules = restriction.page_rules
            button_rules = restriction.button_rules
            for rule in button_rules:
                data[restriction.model_name]['buttons'].update(self.get_button_values(rule))
            for rule in page_rules:
                data[restriction.model_name]['pages'].update(self.get_page_values(rule))

        return data
