from odoo import api, models, fields
from odoo.exceptions import UserError


class Partner(models.Model):

    _inherit = 'res.partner'

    consignee = fields.Boolean('Consignee', tracking=20)
    consignee_location_id = fields.Many2one('stock.location', 
                                            domain=[('usage', '=', 'internal')], 
                                            tracking=22)

    def _prepare_consignment_location_values(self, name, company):
        if not company.consignment_warehouse_id:
            raise UserError('Please configure consignment warehouse in inventory settings.')
        return {
            'name': name,
            'location_id': company.consignment_warehouse_id.lot_stock_id.id,
            'usage': 'internal',
            'company_id': company.id,
        }

    @api.model
    def create(self, vals):
        consignee = vals.get('consignee')
        if not consignee:
            return super().create(vals)
        company = self.env['res.company'].browse(vals.get('company_id')) or self.env.company
        vals['consignee_location_id'] = self.env['stock.location'].create(
            self._prepare_consignment_location_values(vals.get('name'), company)
        ).id
        return super().create(vals)
    
    def write(self, vals):
        if not vals.get('consignee'):
            return super().write(vals)
        res = super().write(vals)
        for partner in self:
            if partner.consignee_location_id:
                continue
            company = partner.company_id or self.env.company
            location = self.env['stock.location'].create(
                self._prepare_consignment_location_values(partner.name, company)
            )
            partner.write({'consignee_location_id': location.id})
        return res
