from odoo import models,fields,api,_
from odoo.exceptions import ValidationError


class DeliveryCarrier(models.Model):

    _inherit = 'delivery.carrier'

    @api.model
    def _get_default_country(self):
        country = self.env['res.country'].search([('code', '=', 'MM')], limit=1)
        return country

    city_id = fields.Many2many('res.city', 'jr_delivery_method_country_rel','jr_delivery_method_id', 'city_id', string='City')
    township_id = fields.Many2many('res.township', 'jr_delivery_method_township_rel','jr_delivery_method_id', 'township_id', string='Township')
    description = fields.Text(string='Description')
    country_id = fields.Many2one('res.country', string='Country', default=_get_default_country)

    @api.constrains('township_id','product_id')
    def _check_township(self):
        for rec in self:
            for township in rec.township_id:

                duplicate = self.search([('id', '!=', rec.id)]).filtered(
                    lambda deli: township.id in deli.township_id.ids
                )
                if duplicate:
                    duplicate_product_id = self.env['delivery.carrier'].sudo().search([('id','!=',rec.id),('product_id','=',rec.product_id.id)])
                        
                    if duplicate_product_id:
                        raise ValidationError(f'Duplicate service product in {township.name} already exists in another shipping method.')
