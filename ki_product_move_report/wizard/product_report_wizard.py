# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError

class ProductMovementReportWizard(models.TransientModel):
    _name = 'product.movement.report.wizard'
    _description = 'Product Movement Report Wizard'

    no_of_months = fields.Integer(
        string="Moving Product in Last(Months)",
        required=True,
        default=1
    )
    company_id = fields.Many2one(
        'res.company',
        string="Company",
        required=True,
        default=lambda self: self.env.user.company_id
    )
    warehouse_ids = fields.Many2many(
        'stock.warehouse',
        string="Warehouses",
        required=True
    )
    group_by_category = fields.Boolean(
        string="Group By Category"
    )
    report_type = fields.Selection(
        selection=[
            ('non_moving', 'Non Moving'),
            ('slow_moving', 'Slow Moving'),
        ],
        default="non_moving",
        string="Report Type",
        required=True
    )

    def action_export_excel(self):
        
        if self.no_of_months < 1:
            raise UserError(
                _('No of months must be greater then zero!')
            )
        
        context = self._context
        datas = {'ids': context.get('active_ids', [])}
        datas['model'] = 'product.movement.report.wizard'
        datas['form'] = self.read()[0]

        for field in datas['form'].keys():
            if isinstance(datas['form'][field], tuple):
                datas['form'][field] = datas['form'][field][0]

        return self.env.ref(
            'ki_product_move_report.product_movement_report_xlsx'
        ).report_action(self, data=datas)
