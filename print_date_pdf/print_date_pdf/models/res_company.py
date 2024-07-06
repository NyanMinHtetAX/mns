from odoo import api, models, fields
import json


class ResCompany(models.Model):
    _inherit = 'res.company'

    printed_reports_name = fields.Text(string='Printed Reports', help='A list of printed reports by report_type.')

    def get_sign_status_for_report(self, report_name, record_ids):
        if not record_ids: return True
        printeds_dict = json.loads(self.printed_reports_name or '{}')

        # Get ids for specified reports,
        printed_ids = printeds_dict.get(report_name, [])
        if not any([r for r in record_ids if r in printed_ids]):
            printeds_dict[report_name] = [*printed_ids, *record_ids]
            self.printed_reports_name = json.dumps(printeds_dict)  # Update values
            not_printed = True
        else:
            # If already printed once
            not_printed = False

        return not_printed
