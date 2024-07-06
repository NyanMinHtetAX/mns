import json
import logging

from odoo import http
from odoo.http import request
from odoo.osv.expression import AND
from odoo.tools import convert


class Controller(http.Controller):

    @http.route('/daily-sale-summary', type='http', auth='user')
    def daily_sale_summary(self, date, team_id, user_id, route_plan_id, **kw):
        r = request.env['report.fs_daily_sale_report.daily_sale_report_template']
        report = request.env.ref('fs_daily_sale_report.daily_sale_summary_report')
        pdf, _ = report.with_context(date=date,
                                     team_id=team_id,
                                     user_id=user_id,
                                     route_plan_id=route_plan_id)._render_qweb_pdf(r)
        pdfhttpheaders = [('Content-Type', 'application/pdf'), ('Content-Length', len(pdf))]
        return request.make_response(pdf, headers=pdfhttpheaders)
