import json

from odoo import fields as odoo_fields, http, tools, _, SUPERUSER_ID
from odoo.exceptions import ValidationError, AccessError, MissingError, UserError, AccessDenied
from odoo.http import content_disposition, Controller, request, route
from odoo.addons.portal.controllers.portal import CustomerPortal
import re
import urllib.parse as urllp
from requests import get

class Py3oPDFPreview(http.Controller):

    @http.route(['/ax/preview_py3o_pdf/'], type='http', auth="public", website=True)
    def preview_py3oPDF_data(self, file_name):
        invoice_id = int(file_name.split('_')[-1])

        # Get Necessary Values
        report_action = request.env.ref('dynamic_pdf_report.action_invoice_b5_pdf_report').read()[0]
        report_action_obj = request.env['ir.actions.report'].browse([report_action['id']])
        invoice = request.env['account.move'].browse(invoice_id)
        datas = invoice.get_invoice_pdf_report(return_data=True)

        # Get Report
        report = getattr(report_action_obj, '_render_py3o')([], data=datas)[0]
        filename = "%s.pdf" % (re.sub('\W+', '-', invoice.name))
        reporthttpheaders = [
            ('Content-Type', 'application/pdf'),
            ('Content-Length', len(report)),
            ('Content-Disposition', "inline; filename=" + filename)
        ]
        return request.make_response(report, headers=reporthttpheaders)

