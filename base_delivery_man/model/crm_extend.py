from odoo import models,fields,api


class CrmTeam(models.Model):
    _inherit = "crm.team"

    member_ids = fields.Many2many(
        'res.users', string='Salespersons',
        domain="[('company_ids', 'in', member_company_ids)]",
        compute='_compute_member_ids', inverse='_inverse_member_ids', search='_search_member_ids',
        help="Users assigned to this team.")