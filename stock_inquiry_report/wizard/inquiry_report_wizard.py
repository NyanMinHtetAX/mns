# -*- coding: utf-8 -*-
import base64
from datetime import datetime
import io
import time
from dateutil import relativedelta
import xlwt
from dateutil.relativedelta import relativedelta

from odoo import models, fields, api, _
from odoo.exceptions import UserError


class StockInquiryReportWizard(models.TransientModel):
    _name = 'stock.inquiry.report.wizard'
    _description = 'Stock Inquiry Report Wizard'
    _rec_name = "location_id"

    company_id = fields.Many2one(
        'res.company',
        string="Company",
        required=True,
        default=lambda self: self.env.user.company_id
    )
    warehouse_id = fields.Many2one(
        'stock.warehouse',
        string="Warehouses",
        required=False
    )
    product_id = fields.Many2one(
        'product.product',
        string="Product",
        required=True,
    )
    product_categ_id = fields.Many2one(
        'product.category',
        string="Product Category",
        required=True,
    )
    date_start = fields.Date(
        string="From Date",
        required=False
    )
    date_end = fields.Date(
        string="To Date",
        required=False
    )
    location_id = fields.Many2one(
        'stock.location',
        string="Location",
        required=True,
    )
    line_ids = fields.One2many(
        'stock.inquiry.report.wizard.lines',
        'wizard_id',
        string="Lines",
        readonly=True
    )
    in_total = fields.Float("In Total", readonly=True, compute='compute_total', default=0.0)
    out_total = fields.Float("Out Total", readonly=True, compute='compute_total', default=0.0)

    style2_title = xlwt.easyxf(
        'font: name Times New Roman, bold on;align: horiz  left;',
        num_format_str='MM/DD/YYYY'
    )
    style2_title_value = xlwt.easyxf(
        'font: name Times New Roman bold on;align: horiz  left;',
        num_format_str='MM/DD/YYYY'
    )
    style2_date = xlwt.easyxf(
        'font: name Times New Roman bold on;align: horiz  right;\
        borders: top thin, bottom thin, left thin, right thin;',
        num_format_str='MM/DD/YYYY'
    )
    table_data_right = xlwt.easyxf(
        'font: name Times New Roman bold on;align: horiz  right;\
        borders: top thin, bottom thin, left thin, right thin;',
        num_format_str='#,##0'
    )
    table_data_left = xlwt.easyxf(
        'font: name Times New Roman bold on;align: horiz left;\
        borders: top thin, bottom thin, left thin, right thin;',
        num_format_str='#,##0'
    )
    table_title = xlwt.easyxf(
        'font: name Times New Roman, bold on;\
        borders: top thin, bottom thin, left thin, right thin;',
        num_format_str='#,##0.00'
    )
    table_title_right = xlwt.easyxf(
        'font: name Times New Roman, bold on; align: horiz right;\
        borders: top thin, bottom thin, left thin, right thin;',
        num_format_str='#,##0.00'
    )

    @api.onchange('product_id')
    def onchange_product(self):
        self.product_categ_id = self.product_id.categ_id

    def compute_total(self):
        if self.line_ids:
            for line in self.line_ids:
                self.in_total += line.in_qty
                self.out_total += line.out_qty
        else:
            self.in_total = 0
            self.out_total = 0

    @api.onchange('warehouse_id')
    def onchange_warehouse(self):
        """
        Make warehouse compatible with company
        """
        location_obj = self.env['stock.location']
        all_locations = location_obj.search([])
        location_ids = location_obj.search([('usage', '=', 'internal')])
        warehouse_id = self.warehouse_id
        if warehouse_id:
            addtional_ids = []
            # for warehouse in total_warehouses:
            store_location_id = warehouse_id.view_location_id.id
            addtional_ids.extend([y.id for y in location_obj.search(
                [('location_id', 'child_of', store_location_id), ('usage', '=', 'internal')])])
            location_ids = addtional_ids
        else:
            location_ids = [p.id for p in all_locations]
        return {
            'domain':
                {
                    'location_id': [('id', 'in', location_ids)]
                },
            'value':
                {
                    'location_id': False
                }
        }

    def action_compute_lines(self):
        self.line_ids = [(6, 0, [])]

        if self.date_start and not self.date_end:
            raise UserError("Please add To Date if you select From Date.")
        if self.date_end and not self.date_start:
            raise UserError("Please add From Date if you select To Date")

        if self.date_start:
            self._cr.execute("""
                SELECT
                    move.id,
                    ps.id as session_id,
                    move.product_uom_qty,
                    0.0 as sale_price,
                    0.0 as cost_price,
                    0.0 as amount,
                    move.reference as reference,
                    sp.sale_customer_id as sale_customer_id,
                    move.origin as description,
                    move.price_unit as price_unit,
                    respartner.id as partner_id,
                    move.date,
                    0 as balance,
                    move.picking_type_id,
                    spt.code,
                    u.factor_ratio,
                    CASE
                        WHEN move.location_id = %s
                        THEN move.product_uom_qty * u.factor_ratio
                        ELSE 0.0
                    END AS out_qty,
                    CASE
                        WHEN move.location_dest_id = %s
                        THEN move.product_uom_qty * u.factor_ratio
                        ELSE 0.0
                    END AS in_qty
                FROM
                    stock_move move
                    LEFT JOIN stock_picking_type spt ON (spt.id=move.picking_type_id)
                    LEFT JOIN stock_picking sp ON (sp.id=move.picking_id)
                    LEFT JOIN pos_session ps ON (ps.id=sp.pos_session_id)
                    LEFT JOIN uom_uom u ON (u.id=move.product_uom)
                    LEFT JOIN res_partner respartner ON (respartner.id=move.partner_id)
                WHERE
                    move.date::date >= %s AND
                    move.date::date <= %s AND
                    (move.location_id = %s OR
                    move.location_dest_id = %s) AND
                    move.product_id = %s AND
                    move.state = 'done'
                ORDER BY
                    move.date
            """, (self.location_id.id,
                  self.location_id.id,
                  self.date_start,
                  self.date_end,
                  self.location_id.id,
                  self.location_id.id,
                  self.product_id.id)
                             )
        else:
            self._cr.execute("""
                SELECT
                    move.id,
                    ps.id as session_id,
                    move.product_uom_qty,
                    0.0 as sale_price,
                    0.0 as cost_price,
                    0.0 as amount,
                    move.reference as reference,
                    sp.sale_customer_id as sale_customer_id,
                    move.origin as description,
                    move.price_unit as price_unit,
                    respartner.id as partner_id,
                    move.date,
                    0 as balance,
                    move.picking_type_id,
                    spt.code,
                    u.factor_ratio,
                    CASE
                        WHEN move.location_id = %s
                        THEN move.product_uom_qty * u.factor_ratio
                        ELSE 0.0
                    END AS out_qty,
                    CASE
                        WHEN move.location_dest_id = %s
                        THEN move.product_uom_qty * u.factor_ratio
                        ELSE 0.0
                    END AS in_qty
                FROM
                    stock_move move
                    LEFT JOIN stock_picking_type spt ON (spt.id=move.picking_type_id)
                    LEFT JOIN stock_picking sp ON (sp.id=move.picking_id)
                    LEFT JOIN pos_session ps ON (ps.id=sp.pos_session_id)
                    LEFT JOIN uom_uom u ON (u.id=move.product_uom)
                    LEFT JOIN res_partner respartner ON (respartner.id=move.partner_id)
                WHERE
                    (move.location_id = %s OR
                    move.location_dest_id = %s) AND
                    move.product_id = %s AND
                    move.state = 'done'
                ORDER BY
                    move.date
            """, (self.location_id.id,
                  self.location_id.id,
                  self.location_id.id,
                  self.location_id.id,
                  self.product_id.id)
                             )
        move_lines_res = self._cr.dictfetchall()
        res = []
        if self.date_start:
            self._cr.execute("""
                    SELECT
                        move.id,
                        move.product_uom_qty,
                        move.picking_type_id,
                        spt.code,
                        u.factor_ratio,
                        CASE
                            WHEN move.location_id = %s
                            THEN move.product_uom_qty * u.factor_ratio
                            ELSE 0.0
                        END AS out_qty,
                        CASE
                            WHEN move.location_dest_id = %s
                            THEN move.product_uom_qty * u.factor_ratio
                            ELSE 0.0
                        END AS in_qty
                    FROM
                        stock_move move
                        LEFT JOIN stock_picking_type spt ON (spt.id=move.picking_type_id)
                        LEFT JOIN uom_uom u ON (u.id=move.product_uom)
                        LEFT JOIN res_partner respartner ON (respartner.id=move.partner_id)
                    WHERE
                        move.date::date < %s AND
                        (move.location_id = %s OR
                        move.location_dest_id = %s) AND
                        move.product_id = %s AND
                        move.state = 'done'
                    ORDER BY
                        move.date
                """, (self.location_id.id,
                      self.location_id.id,
                      self.date_start,
                      self.location_id.id,
                      self.location_id.id,
                      self.product_id.id)
                             )

            res = self._cr.dictfetchall()

        begining_qty = 0.0
        if res:
            for r in res:
                begining_qty = begining_qty + r['in_qty'] - r['out_qty']

        standard_price = self.product_id.price_compute('standard_price')[self.product_id.id]
        list_price = self.product_id.price_compute('list_price')[self.product_id.id]
        for l in move_lines_res:
            if l.get('in_qty', 0.0) > 0.0:
                begining_qty += l['in_qty']
                l['balance'] = begining_qty
            elif l.get('out_qty', 0.0):
                begining_qty -= l['out_qty']
                l['balance'] = begining_qty
            if l['code'] is not None and l['code'] == 'outgoing':
                l['sale_price'] = list_price
                l['amount'] = l['product_uom_qty'] * l['factor_ratio'] * list_price
            else:
                l['cost_price'] = standard_price
            if l['code'] is not None and l['code'] == 'outgoing':
                l['price_unit'] = 0.0
            elif l['code'] is not None and l['code'] == 'internal':
                l['price_unit'] = 0.0
            else:
                price = l['price_unit'] or 0.0
                qty = l['product_uom_qty'] * l['factor_ratio'] or 0.0

                l['price_unit'] = price
                l['amount'] = qty * price

        lines = [(0, 0, l) for l in move_lines_res]
        self.line_ids = lines

    def action_export_excel(self):
        self.action_compute_lines()
        print_date = (datetime.now() + relativedelta(hours=6, minutes=30)).strftime('%Y-%m-%d - %H:%M:%S')

        workbook = xlwt.Workbook()
        sheet = workbook.add_sheet('Stock Inquiry')

        row_count = 0
        sheet.write(row_count, 0, "Company", self.style2_title)
        sheet.write(row_count, 1, self.company_id.display_name, self.style2_title_value)
        sheet.write(row_count, 5, "Print Date", self.style2_title)
        sheet.write(row_count, 6, str(print_date), self.style2_title)

        row_count += 1
        sheet.write(row_count, 0, "Product", self.style2_title)
        sheet.write(row_count, 1, self.product_id.display_name, self.style2_title_value)
        sheet.write(row_count, 5, "Date From", self.style2_title)
        sheet.write(row_count, 6, self.date_start, self.style2_title_value)

        row_count += 1
        sheet.write(row_count, 0, "Product Category", self.style2_title)
        sheet.write(row_count, 1, self.product_categ_id.display_name or '', self.style2_title_value)
        sheet.write(row_count, 5, "To Date", self.style2_title)
        sheet.write(row_count, 6, self.date_end, self.style2_title_value)

        row_count += 1
        sheet.write(row_count, 0, "Warehouse", self.style2_title)
        sheet.write(row_count, 1, self.warehouse_id.display_name or '', self.style2_title_value)
        sheet.write(row_count, 5, "Location", self.style2_title)
        sheet.write(row_count, 6, self.location_id.display_name or '', self.style2_title_value)

        row_count += 2

        # Table Header
        sheet.write(
            row_count, 0,
            "#", self.table_title
        )
        sheet.write(
            row_count, 1,
            "Date", self.table_title_right
        )
        sheet.write(
            row_count, 2,
            "Stock Picking No", self.table_title
        )
        sheet.write(
            row_count, 3,
            "POS Session No", self.table_title
        )
        sheet.write(
            row_count, 4,
            "Source Doc", self.table_title
        )
        sheet.write(
            row_count, 5,
            "Name", self.table_title
        )
        sheet.write(
            row_count, 6,
            "Sale Customer", self.table_title
        )
        sheet.write(
            row_count, 7,
            "IN", self.table_title_right
        )
        sheet.write(
            row_count, 8,
            "OUT", self.table_title_right
        )
        sheet.write(
            row_count, 9,
            "BALANCE", self.table_title_right
        )
        sheet.write(
            row_count, 10,
            "PURCHASE PRICE", self.table_title_right
        )
        sheet.write(
            row_count, 11,
            "SALE PRICE", self.table_title_right
        )
        sheet.write(
            row_count, 12,
            "AMOUNT", self.table_title_right
        )

        # table values
        row_count += 1
        count = 1
        for line in self.line_ids:
            sheet.write(
                row_count, 0,
                count, self.table_data_left
            )
            count += 1
            sheet.write(
                row_count, 1,
                line.date,
                self.style2_date
            )
            sheet.write(
                row_count, 2,
                line.reference,
                self.table_data_left
            )
            sheet.write(
                row_count, 3,
                line.session_id.name,
                self.table_data_left
            )
            sheet.write(
                row_count, 4,
                line.description,
                self.table_data_left
            )
            sheet.write(
                row_count, 5,
                line.partner_id.name,
                self.table_data_left)

            sheet.write(
                row_count, 6,
                line.sale_customer_id.name,
                self.table_data_left)

            sheet.write(
                row_count, 7,
                line.in_qty,
                self.table_data_right
            )
            sheet.write(
                row_count, 8,
                line.out_qty,
                self.table_data_right
            )
            sheet.write(
                row_count, 9,
                line.balance,
                self.table_data_right
            )

            sheet.write(
                row_count, 10,
                line.price_unit,
                self.table_data_right
            )
            sheet.write(
                row_count, 11,
                line.sale_price,
                self.table_data_right
            )
            sheet.write(
                row_count, 12,
                line.amount,
                self.table_data_right
            )

            row_count += 1

        sheet.write(
            row_count, 4,
            "TOTAL",
            self.table_title
        )
        sheet.write(
            row_count, 5,
            self.in_total,
            self.table_data_right
        )
        sheet.write(
            row_count, 6,
            self.out_total,
            self.table_data_right
        )
        stream = io.BytesIO()

        workbook.save(stream)
        attach_id = self.env['stock.inquiry.excel.output'].create({
            'name': str(self.date_start) + '.xls',
            'filename': base64.encodestring(
                stream.getvalue()
            )
        })
        return {
            'type': 'ir.actions.act_window',
            'name': ('Report'),
            'res_model': 'stock.inquiry.excel.output',
            'res_id': attach_id.id,
            'view_type': 'form',
            'view_mode': 'form',
            'target': 'new',
        }

class StockInquiryReportWizardLines(models.TransientModel):
    _name = 'stock.inquiry.report.wizard.lines'
    _description = 'Stock Inquiry Report Wizard Lines'

    date = fields.Datetime(
        string="Date"
    )
    reference = fields.Char(
        string="Stock Picking No"
    )
    description = fields.Char(
        string="Source Doc"
    )
    partner_id = fields.Many2one(
        "res.partner", string="Name")

    sale_customer_id = fields.Many2one(
        "res.partner", string="Sale Customer",)

    product_uom_qty = fields.Float(
        string="Demand"
    )
    picking_type_id = fields.Many2one(
        "stock.picking.type", string="Operation Type")
    code = fields.Char("code")

    in_qty = fields.Float(
        string="IN"
    )
    out_qty = fields.Float(
        string="OUT"
    )
    balance = fields.Float(
        string="BALANCE"
    )
    cost_price = fields.Float(
        string="COST PRICE"
    )
    sale_price = fields.Float(
        string="SALE PRICE"
    )
    amount = fields.Float(
        string="AMOUNT"
    )
    price_unit = fields.Float(string="PURCHASE PRICE")
    wizard_id = fields.Many2one(
        'stock.inquiry.report.wizard',
        string="Wizard"
    )
    factor_ratio = fields.Float()
    session_id = fields.Many2one('pos.session', 'POS Session No')


class Output(models.TransientModel):
    _name = 'stock.inquiry.excel.output'
    _description = 'Excel Report Output'

    name = fields.Char(
        string='File Name',
        size=256,
        readonly=True
    )
    filename = fields.Binary(
        string='File to Download',
        readonly=True
    )
