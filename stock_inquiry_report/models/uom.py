from odoo import models, fields, api, _
from odoo.exceptions import UserError


class UoM(models.Model):
    _inherit = 'uom.uom'

    @api.depends('factor')
    def _compute_factor_ratio(self):
        self.factor_ratio = 0.0
        for uom in self:
            uom.factor_ratio = uom.factor and (1.0 / uom.factor) or 0.0

    factor_ratio = fields.Float('Bigger Ratio', compute='_compute_factor_ratio', digits=0,
                                readonly=True,  store=True)

   
