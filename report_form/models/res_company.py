from odoo import models, fields, api, tools, _


class Company(models.Model):
    _inherit = "res.company"

    fax_no = fields.Char('FAX No')
    service_phone = fields.Char('Service Phone')
    service_mail = fields.Char('Service Email')
    shop1_add = fields.Char('Shop-1 Address')
    shop1_phone = fields.Char('Shop-1 Phone')
    shop1_fax = fields.Char('Shop-1 FAX')
    shop2_add = fields.Char('Shop-2 Address')
    shop2_phone = fields.Char('Shop-2 Phone')
    shop2_fax = fields.Char('Shop-2 FAX')
