from odoo import api, models, fields


class FieldSalePaymentMethod(models.Model):

    _inherit = "fieldsale.payment.method"

    team_ids = fields.Many2many('crm.team',
                                'sales_team_payment_methods',
                                'payment_id',
                                'team_id', 'Sales Teams')