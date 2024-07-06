from odoo import models, fields, api, _


class Partner(models.Model):
    _inherit = "res.partner"

    code = fields.Char(string='Code')
    outlet_type = fields.Many2one('res.partner.outlet', string='Outlet Type')
    is_credit_limit = fields.Boolean(string='Customer Credit Limit', default=False)
    is_mobile_customer = fields.Boolean(string='Mobile Customer', default=False)
    latitude = fields.Float('Latitude', digits=(24, 12))
    longitude = fields.Float('Longitude', digits=(24, 12))
    sale_channel_ids = fields.Many2many('res.sale.channel', 'partner_sale_channel_rel', 'partner_id', 'channel_id', 'Sale Channels')
    partner_latitude = fields.Float(compute='_compute_partner_lat_lng', store=True, digits=(24, 12))
    partner_longitude = fields.Float(compute='_compute_partner_lat_lng', store=True, digits=(24, 12))
    custom_payment_for_sale = fields.Many2one('account.payment.term', "Payment Term for Sale", compute='get_sale_payment_term', store=True)
    custom_payment_for_purchase = fields.Many2one('account.payment.term', "Payment Term for Purchase", compute='get_purchase_payment_term',store=True)
    
    @api.depends('property_payment_term_id')
    def get_sale_payment_term(self):
        for rec in self:
            rec.custom_payment_for_sale = rec.property_payment_term_id.id

    @api.depends('property_supplier_payment_term_id')
    def get_purchase_payment_term(self):
        for rec in self:
            rec.custom_payment_for_purchase = rec.property_supplier_payment_term_id.id

    @api.depends('latitude', 'longitude')
    def _compute_partner_lat_lng(self):
        for partner in self:
            partner.partner_latitude = partner.latitude
            partner.partner_longitude = partner.longitude

    @api.onchange("outlet_type")
    def onchange_outlet_type(self):
        if self.outlet_type:
            self.sale_channel_ids = [(6, 0, self.outlet_type.channel_id.ids)]

    def generate_sequence_code(self):
        for partner in self:
            if partner.customer or partner.supplier or partner.is_mobile_customer:
                if partner.customer:
                    sequence_id = partner.state_id.customer_sequence_id
                elif partner.is_mobile_customer:
                    sequence_id = partner.state_id.customer_sequence_id
                    partner.write({
                        'customer': True,
                        'is_mobile_customer': False,
                    })
                else:
                    sequence_id = partner.state_id.supplier_sequence_id
                if sequence_id:
                    partner.ref = sequence_id.next_by_id()
                else:
                    raise exceptions.ValidationError(f'Sequence is missing for some partner\'s state.')


class ResTownship(models.Model):
    _inherit = "res.township"

    @api.model
    def create(self, values):
        township = super(ResTownship, self).create(values)
        name = values.get('name')
        code = values.get('code')
        seq_vals = {

            'name': name + ' Sequence',
            'code': (code) + '.' + '-township-' + '.sequence',
            'active': True,
            'implementation': 'no_gap',
            'prefix': (code) + '%(y)s' + '%(month)s' + '%(day)s',
            'padding': 4,
            'number_increment': 1,
            'number_next_actual': 1,
        }
        self.env['ir.sequence'].sudo().create(seq_vals)
        return township


class Team(models.Model):
    _inherit = 'crm.team'

    code = fields.Char(string='Code')
