from odoo import api, models, fields


class Company(models.Model):

    _inherit = 'res.company'

    expired_lot_block_a_duration = fields.Float('Block A Duration')
    expired_lot_block_a_duration_unit = fields.Selection([('days', 'Days'),
                                                          ('months', 'Months'),
                                                          ('years', 'Years')], 'Block A Duration Unit')
    expired_lot_block_a_color = fields.Char('Block A Color')
    expired_lot_block_b_duration = fields.Float('Block B Duration')
    expired_lot_block_b_duration_unit = fields.Selection([('days', 'Days'),
                                                          ('months', 'Months'),
                                                          ('years', 'Years')], 'Block B Duration Unit')
    expired_lot_block_b_color = fields.Char('Block B Color')
    expired_lot_block_c_duration = fields.Float('Block C Duration')
    expired_lot_block_c_duration_unit = fields.Selection([('days', 'Days'),
                                                          ('months', 'Months'),
                                                          ('years', 'Years')], 'Block C Duration Unit')
    expired_lot_block_c_color = fields.Char('Block C Color')
    expired_lot_color = fields.Char('Expired Lot Color')


class ResConfigSettings(models.TransientModel):

    _inherit = 'res.config.settings'

    expired_lot_block_a_duration = fields.Float('Block A Duration', related='company_id.expired_lot_block_a_duration', readonly=False)
    expired_lot_block_a_duration_unit = fields.Selection(string='Block A Duration Unit', related='company_id.expired_lot_block_a_duration_unit', readonly=False)
    expired_lot_block_a_color = fields.Char('Block A Color', related='company_id.expired_lot_block_a_color', readonly=False)
    expired_lot_block_b_duration = fields.Float('Block B Duration', related='company_id.expired_lot_block_b_duration', readonly=False)
    expired_lot_block_b_duration_unit = fields.Selection(string='Block B Duration Unit', related='company_id.expired_lot_block_b_duration_unit', readonly=False)
    expired_lot_block_b_color = fields.Char('Block B Color', related='company_id.expired_lot_block_b_color', readonly=False)
    expired_lot_block_c_duration = fields.Float(string='Block C Duration', related='company_id.expired_lot_block_c_duration', readonly=False)
    expired_lot_block_c_duration_unit = fields.Selection(string='Block C Duration Unit', related='company_id.expired_lot_block_c_duration_unit', readonly=False)
    expired_lot_block_c_color = fields.Char('Block C Color', related='company_id.expired_lot_block_c_color', readonly=False)
    expired_lot_color = fields.Char('Expired Lot Color', related='company_id.expired_lot_color', readonly=False)

