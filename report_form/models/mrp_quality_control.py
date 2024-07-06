from odoo import models, fields, api, tools, _


class MRPQualityControl(models.Model):
    _inherit = 'mrp.quality.control'

    def get_mc_pdf(self):
        records = []
        status = ''

        for rec in self:
            if rec.status == 'pass':
                status = 'Passed'
            elif rec.status == 'reject':
                status = 'Rejected'
            else:
                status = ''
            records.append({
                'image': self.env.company.logo,
                'ref': rec.reference_no,
                'type': rec.type or '',
                'code': rec.code_no or '',
                'batch': rec.batch_no or '',
                'status': status or '',
                'mo': rec.production_id.name if rec.production_id else '',
                'formula': rec.formula_no or '',
                'date': rec.mo_date.strftime('%d-%m-%Y') if rec.mo_date else '',
                'qty': rec.mo_qty or '',
                'uom': rec.product_uom_id.name if rec.product_uom_id else '',
                'remark': rec.remark or '',
            })
            return self.env.ref('report_form.action_qc_pdf').report_action(self, data={
                'records': records,
            })
