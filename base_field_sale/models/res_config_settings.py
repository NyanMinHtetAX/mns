from odoo import api, models, fields


class Company(models.Model):

    _inherit = 'res.company'

    fs_usage_status = fields.Selection([('online', 'Online'),
                                        ('offline', 'Offline')], 'Usage Status', default='offline')
    fs_primary_color = fields.Char('FS Primary Color')
    fs_secondary_color = fields.Char('FS Secondary Color')
    fs_map_api_key = fields.Char('Map API Key')
    fs_sms_api_key = fields.Char('SMS API Key')
    fs_onesignal_app_id = fields.Char('Onesignal App ID')
    fs_data_storage_period = fields.Integer('Data Storage Period')
    fs_use_tax = fields.Boolean('Use Tax')
    fs_map_max_distance = fields.Float('Map Max Distance')
    fs_payment_collection_assigned_type = fields.Selection([('by_account_department', 'By Account Department'),
                                                            ('by_cash_collector', 'By Cash Collector')], 'Payment Collection Assigned Type',
                                                           required=1,
                                                           default='by_account_department')

    van_storage = fields.Selection(
        [('daily_s_keep', 'Daily Stock Keep'), ('daily_s_n_keep', 'Daily Stock Not Keep')], default='daily_s_n_keep',
        string='Van Order Storage')


class ResConfigSettings(models.TransientModel):

    _inherit = 'res.config.settings'

    fs_primary_color = fields.Char('Primary Color', related='company_id.fs_primary_color', readonly=False)
    fs_secondary_color = fields.Char('Secondary Color', related='company_id.fs_secondary_color', readonly=False)
    fs_map_api_key = fields.Char('Map API Key', related='company_id.fs_map_api_key', readonly=False)
    fs_sms_api_key = fields.Char('SMS API Key', related='company_id.fs_sms_api_key', readonly=False)
    fs_onesignal_app_id = fields.Char('Onesignal App ID', related='company_id.fs_onesignal_app_id', readonly=False)
    fs_data_storage_period = fields.Integer('Data Storage Period', related='company_id.fs_data_storage_period', readonly=False)
    fs_payment_collection_assigned_type = fields.Selection(string='Payment Collection Assigned Type', related='company_id.fs_payment_collection_assigned_type', readonly=False, required=1)
    fs_use_tax = fields.Boolean('Use Tax', related='company_id.fs_use_tax', readonly=False)
    fs_usage_status = fields.Selection(string='Usage Status', related='company_id.fs_usage_status', readonly=False)
    fs_map_max_distance = fields.Float('Map Max Distance', related='company_id.fs_map_max_distance', readonly=False)
    fs_van_storage = fields.Selection(string='Van Order Storage', related='company_id.van_storage', readonly=False)
