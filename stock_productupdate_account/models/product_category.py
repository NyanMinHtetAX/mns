from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
from odoo.tools import format_amount

ACCOUNT_DOMAIN = "['&', '&', '&', ('deprecated', '=', False), ('internal_type','=','other'), ('company_id', '=', current_company_id), ('is_off_balance', '=', False)]"


class ProductCategory(models.Model):
    _inherit = "product.category"

    property_counter_part_account_id = fields.Many2one('account.account', company_dependent=True,
                                                       string="Counter-Part Account",
                                                       domain=ACCOUNT_DOMAIN,
                                                       help="This account will be used when changing a product cost.")