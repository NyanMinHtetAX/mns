from odoo import api, fields, models, tools, _
from odoo.exceptions import UserError
import re


class Country(models.Model):

    _inherit = 'res.country'

    township_id = fields.Many2one('res.township', string='Township', ondelete='restrict')
    code = fields.Char(string='Code',
                       size=10,
                       help='The ISO country code in two chars. \nYou can use this field for quick search.')
    address_format = fields.Text(string="Layout in Reports",
                                 help="Display format to use for addresses belonging to this country.\n\n"
                                      "You can use python-style string pattern with all the fields of the address "
                                      "(for example, use '%(street)s' to display the field 'street') plus"
                                      "\n%(township_name)s: the name of the township"
                                      "\n%(state_name)s: the name of the state"
                                      "\n%(state_code)s: the code of the state"
                                      "\n%(country_name)s: the name of the country"
                                      "\n%(country_code)s: the code of the country",
                                 default='%(street)s\n%(street2)s\n%(township_name)s %(city)s\n%(state_code)s %('
                                         'zip)s\n%(country_name)s')

    def get_address_fields(self):
        self.ensure_one()
        return re.findall(r'\((.+?)\)', self.address_format)

    @api.constrains('address_format')
    def _check_address_format(self):
        for record in self:
            if record.address_format:
                address_info = [
                    'state_code',
                    'state_name',
                    'country_code',
                    'country_name',
                    'company_name',
                    'township_name'
                ]
                address_fields = self.env['res.partner']._formatting_address_fields() + address_info
                try:
                    record.address_format % {address_field: 1 for address_field in address_fields}
                except (ValueError, KeyError):
                    raise UserError(_('The layout contains an invalid format key'))
