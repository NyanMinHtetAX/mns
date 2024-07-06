from odoo import api, models, fields


class IrConfigParameter(models.Model):

    _inherit = "ir.config_parameter"

    @api.model
    def get_web_m2x_options(self):
        opts = [
            "web_m2x_options.create",
            "web_m2x_options.create_edit",
            "web_m2x_options.limit",
            "web_m2x_options.search_more",
            "web_m2x_options.m2o_dialog",
        ]
        return self.sudo().search_read([["key", "in", opts]], ["key", "value"])


class ResConfigSettings(models.TransientModel):

    _inherit = 'res.config.settings'

    is_foc = fields.Boolean('Sale FOC Item Discount', related='company_id.is_foc', readonly=False)
    foc_discount_account_id = fields.Many2one('account.account', 'Sale FOC Item Discount Account',
                                              related='company_id.foc_discount_account_id',
                                              readonly=False)

    @api.onchange('company_id')
    def onchange_company_id(self):
        for res in self:
            res.is_foc = res.company_id.is_foc
            res.foc_discount_account_id = res.company_id.foc_discount_account_id
