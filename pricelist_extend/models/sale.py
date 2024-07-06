from odoo import models, fields, api, _


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    @api.onchange('partner_id')
    def onchange_partner_domain_pricelist(self):
        if self.partner_id:
            pricelist = self.partner_id.pricelist_ids.ids
            self.pricelist_id = False
            if len(pricelist) > 0:
                self.pricelist_id = pricelist[0]
            return {'domain': {'pricelist_id': [('id', 'in', pricelist)]}}
        else:
            return {'domain': {'pricelist_id': []}}

