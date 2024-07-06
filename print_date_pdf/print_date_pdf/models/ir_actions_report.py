from odoo import api, models, fields


class IrActionsReport(models.Model):
    _inherit = 'ir.actions.report'

    def _render_qweb_pdf(self, res_ids=None, data=None):
        # Overridden so that the print > actions will decide to show or not to show Odoo sign on PDF Footer .
        default_company = self.env['res.company'].search([], limit=1)
        if isinstance(res_ids, int):
            res_ids = [res_ids]
        not_printed = default_company.get_sign_status_for_report(self.report_name, res_ids)
        data = data and dict(data) or {}
        data.update({'display_odoo_sign_in_footer': True if not_printed else False})
        return super()._render_qweb_pdf(res_ids=res_ids, data=data)
