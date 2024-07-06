from odoo import models, fields, api, _


class Company(models.Model):
    _inherit = "res.company"

    customer_visit = fields.Boolean(string='Customer Visit',default=False)
    pre_sale_order = fields.Boolean(string='Pre Sale Order', default=False)
    stock_exchange = fields.Boolean(string='Stock Exchange', default=False)
    stock_damage = fields.Boolean(string='Stock Damage', default=False)
    stock_request = fields.Boolean(string='Stock Request', default=False)
    stock_return = fields.Boolean(string='Stock Return', default=False)

    check_admin = fields.Boolean(string='Admin?',compute='_get_admin_access')

    def _get_admin_access(self):
        if self.env.user._is_admin():
            self.check_admin = True
        else:
            self.check_admin = False



