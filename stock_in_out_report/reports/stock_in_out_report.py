import pytz
import logging
from itertools import groupby
from odoo import api, models, fields
from datetime import datetime
from dateutil.relativedelta import relativedelta
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT

_logger = logging.getLogger(__name__)

QUERY = """

SELECT      {0},
            LOCATION_ID,
            SUM(ROUND(PURCHASE_QTY)) AS PURCHASE_QTY,
            SUM(ROUND(PURCHASE_RETURN_QTY)) AS PURCHASE_RETURN_QTY,
            SUM(ROUND(SALE_QTY)) AS SALE_QTY,
            SUM(ROUND(SALE_RETURN_QTY)) AS SALE_RETURN_QTY,    
            SUM(ROUND(POS_QTY)) AS POS_QTY,
            SUM(ROUND(POS_RETURN_QTY)) AS POS_RETURN_QTY,                    
            SUM(ROUND(INTERNAL_TRANSFER_QTY)) AS INTERNAL_TRANSFER_QTY,
            SUM(ROUND(ADJUSTMENT_QTY)) AS ADJUSTMENT_QTY,
            SUM(ROUND(SCRAP_QTY)) AS SCRAP_QTY
FROM
(
SELECT      SML.PRODUCT_ID,
            PT.CATEG_ID AS CATEGORY_ID,
            CASE
                WHEN SL.USAGE='internal' THEN SL.ID
                WHEN DL.USAGE='internal' THEN DL.ID
                ELSE NULL
            END AS LOCATION_ID,
            CASE
                WHEN SM.PURCHASE_LINE_ID IS NOT NULL AND SL.USAGE='supplier' AND DL.USAGE='internal' AND DL.ID IN {1}
                THEN (SML.QTY_DONE / L_UOM.FACTOR) * P_UOM.FACTOR
                ELSE 0
            END AS PURCHASE_QTY,
            CASE
                WHEN SM.PURCHASE_LINE_ID IS NOT NULL AND SL.USAGE='internal' AND DL.USAGE='supplier' AND SL.ID IN {2}
                THEN (-SML.QTY_DONE / L_UOM.FACTOR) * P_UOM.FACTOR
                ELSE 0
            END AS PURCHASE_RETURN_QTY,
            CASE
                WHEN SM.SALE_LINE_ID IS NOT NULL AND SL.USAGE='internal' AND DL.USAGE='customer' AND SL.ID IN {3}
                THEN (-SML.QTY_DONE / L_UOM.FACTOR) * P_UOM.FACTOR
                ELSE 0
            END AS SALE_QTY,
            CASE
                WHEN SM.SALE_LINE_ID IS NOT NULL AND SL.USAGE='customer' AND DL.USAGE='internal' AND DL.ID IN {4}
                THEN (SML.QTY_DONE / L_UOM.FACTOR) * P_UOM.FACTOR
                ELSE 0
            END AS SALE_RETURN_QTY,
             
            CASE
                WHEN SM.ANALYTIC_ACCOUNT_ID IS NOT NULL AND SL.USAGE='internal' AND DL.USAGE='customer' AND SL.ID IN {5}
                THEN (-SML.QTY_DONE / L_UOM.FACTOR) * P_UOM.FACTOR
                ELSE 0
            END AS POS_QTY,
            CASE
                WHEN SM.ANALYTIC_ACCOUNT_ID IS NOT NULL AND SL.USAGE='customer' AND DL.USAGE='internal' AND DL.ID IN {6}
                THEN (SML.QTY_DONE / L_UOM.FACTOR) * P_UOM.FACTOR
                ELSE 0
            END AS POS_RETURN_QTY,
            
            CASE
                WHEN SL.USAGE='internal' AND DL.USAGE='internal' AND SL.ID IN {7}
                THEN (-SML.QTY_DONE / L_UOM.FACTOR) * P_UOM.FACTOR
                ELSE 0
            END AS INTERNAL_TRANSFER_QTY,
            CASE
                WHEN SL.USAGE='inventory' AND DL.USAGE='internal' AND SM.SCRAPPED!=TRUE AND DL.ID IN {8}
                THEN (SML.QTY_DONE / L_UOM.FACTOR) * P_UOM.FACTOR
                WHEN SL.USAGE='internal' AND DL.USAGE='inventory' AND SM.SCRAPPED!=TRUE AND SL.ID IN {9}
                THEN (-SML.QTY_DONE / L_UOM.FACTOR) * P_UOM.FACTOR
                ELSE 0
            END AS ADJUSTMENT_QTY,
            CASE
                WHEN SL.SCRAP_LOCATION=TRUE AND DL.USAGE='internal' AND SM.SCRAPPED=TRUE AND DL.ID IN {10}
                THEN (SML.QTY_DONE / L_UOM.FACTOR) * P_UOM.FACTOR
                WHEN SL.USAGE='internal' AND DL.SCRAP_LOCATION=TRUE AND SM.SCRAPPED=TRUE AND SL.ID IN {11}
                THEN (-SML.QTY_DONE / L_UOM.FACTOR) * P_UOM.FACTOR
                ELSE 0
            END AS SCRAP_QTY
            
            
FROM        STOCK_MOVE_LINE SML
            LEFT JOIN STOCK_MOVE SM ON SML.MOVE_ID=SM.ID
            LEFT JOIN STOCK_LOCATION SL ON SL.ID=SML.LOCATION_ID
            LEFT JOIN STOCK_LOCATION DL ON DL.ID=SML.LOCATION_DEST_ID
            LEFT JOIN PRODUCT_PRODUCT PP ON PP.ID=SM.PRODUCT_ID
            LEFT JOIN PRODUCT_TEMPLATE PT ON PT.ID=PP.PRODUCT_TMPL_ID
            LEFT JOIN PRODUCT_CATEGORY PC ON PC.ID=PT.CATEG_ID
            LEFT JOIN UOM_UOM P_UOM ON P_UOM.ID=PT.UOM_ID
            LEFT JOIN UOM_UOM L_UOM ON L_UOM.ID=SML.PRODUCT_UOM_ID
            
WHERE       SML.DATE >= '{12}' AND SML.DATE <= '{13}' AND SML.STATE='done' AND SML.PRODUCT_ID IN {14}
            AND (SL.ID IN {15} OR DL.ID IN {16})
            
UNION ALL

SELECT      SML.PRODUCT_ID,
            PT.CATEG_ID AS CATEGORY_ID,
            SML.LOCATION_DEST_ID AS LOCATION_ID,
            0 AS PURCHASE_QTY,
            0 AS PURCHASE_RETURN_QTY,
            0 AS SALE_QTY,
            0 AS SALE_RETURN_QTY,
            0 AS POS_QTY,
            0 AS POS_RETURN_QTY,
            (SML.QTY_DONE / L_UOM.FACTOR) * P_UOM.FACTOR AS INTERNAL_TRANSFER_QTY,
            0 AS ADJUSTMENT_QTY,
            0 AS SCRAP_QTY

FROM        STOCK_MOVE_LINE SML
            LEFT JOIN STOCK_MOVE SM ON SML.MOVE_ID=SM.ID
            LEFT JOIN STOCK_LOCATION SL ON SL.ID=SML.LOCATION_ID
            LEFT JOIN STOCK_LOCATION DL ON DL.ID=SML.LOCATION_DEST_ID
            LEFT JOIN PRODUCT_PRODUCT PP ON PP.ID=SM.PRODUCT_ID
            LEFT JOIN PRODUCT_TEMPLATE PT ON PT.ID=PP.PRODUCT_TMPL_ID
            LEFT JOIN PRODUCT_CATEGORY PC ON PC.ID=PT.CATEG_ID
            LEFT JOIN UOM_UOM P_UOM ON P_UOM.ID=PT.UOM_ID
            LEFT JOIN UOM_UOM L_UOM ON L_UOM.ID=SML.PRODUCT_UOM_ID
            
WHERE       SML.DATE >= '{17}' AND SML.DATE <= '{18}' AND SML.STATE='done' AND SML.PRODUCT_ID IN {19}
            AND SL.USAGE='internal' AND DL.USAGE='internal' AND DL.ID IN {20}

) AS DATA

GROUP BY LOCATION_ID, {21}

ORDER BY LOCATION_ID
"""


class StockInOutReport(models.AbstractModel):
    _name = 'report.stock_in_out_report.stock_in_out_report'
    _description = 'Stock I/O Report'
    _inherit = 'report.report_xlsx.abstract'

    def generate_xlsx_report(self, workbook, data, objects):
        tz = pytz.timezone(self.env.context.get('tz'))
        print_date = (datetime.now() + relativedelta(hours=6, minutes=30)).strftime('%Y-%m-%d - %H:%M:%S')
        start_date_raw = datetime.strptime(data['start_date'], DEFAULT_SERVER_DATE_FORMAT)
        end_date_raw = datetime.strptime(data['end_date'] + ' 23:59:59', DEFAULT_SERVER_DATETIME_FORMAT)
        start_date = tz.localize(start_date_raw).astimezone(pytz.utc)
        end_date = tz.localize(end_date_raw).astimezone(pytz.utc)
        warehouse_ids = self.env['stock.warehouse'].browse(data['warehouse_ids'])
        location_ids = self.env['stock.location'].browse(data['location_ids'])
        category_ids = self.env['product.category'].browse(data['category_ids'])
        product_ids = self.env['product.product'].browse(data['product_ids'])
        based_on = data['based_on']

        sheet = workbook.add_worksheet('Stock In/Out Report')
        topmost_cell = workbook.add_format({
            'font_name': 'Arial', 'font_size': 11, 'text_wrap': True,
            'valign': 'vcenter', 'align': 'center', 'bold': True,
        })
        header_cell = workbook.add_format({
            'font_name': 'Arial', 'font_size': 10, 'text_wrap': True,
            'valign': 'vcenter', 'align': 'center', 'bold': True, 'border': 1,
        })
        header_cell_left = workbook.add_format({
            'font_name': 'Arial', 'font_size': 10, 'text_wrap': True,
            'valign': 'vcenter', 'align': 'left', 'bold': True, 'border': 1,
        })

        sheet.set_row(0, 25)

        sheet.set_column('A:A', 5)
        sheet.set_column('B:B', 30)
        sheet.set_column('C:C', 25)
        sheet.set_column('D:D', 20)
        sheet.set_column('E:E', 18)
        sheet.set_column('F:O', 15)

        sheet.merge_range('A1:O1', 'Stock In/Out Report', topmost_cell)
        sheet.merge_range('A3:B3', 'Company', header_cell_left)
        sheet.write('C3', self.env.company.name, header_cell_left)
        sheet.merge_range('A4:B4', 'Warehouse', header_cell_left)
        sheet.write('C4', ', '.join(warehouse_ids.mapped('name')), header_cell_left)
        sheet.merge_range('A5:B5', 'Location', header_cell_left)
        sheet.write('C5', ', '.join(location_ids.mapped('complete_name')), header_cell_left)
        sheet.merge_range('A6:B6', 'Beginning Date', header_cell_left)
        sheet.write('C6', start_date_raw.strftime('%d %B, %Y'), header_cell_left)
        sheet.merge_range('A7:B7', 'Ending Date', header_cell_left)
        sheet.write('C7', end_date_raw.strftime('%d %B, %Y'), header_cell_left)

        sheet.write('K3', 'Print Date -', header_cell_left)
        sheet.merge_range('L3:M3', str(print_date), header_cell_left)

        sheet.write('A10', 'No.', header_cell)
        sheet.write('B10', 'Item', header_cell)
        sheet.write('C10', 'Category', header_cell)
        sheet.write('D10', 'Internal Reference', header_cell)
        sheet.write('E10', 'Opening Qty', header_cell)
        sheet.write('F10', 'Purchase Qty', header_cell)
        sheet.write('G10', 'Purchase Return Qty', header_cell)
        sheet.write('H10', 'Sale Qty', header_cell)
        sheet.write('I10', 'Sale Return Qty', header_cell)
        sheet.write('J10', 'POS Qty', header_cell)
        sheet.write('K10', 'POS Return Qty', header_cell)
        sheet.write('L10', 'Internal Transfer Qty', header_cell)
        sheet.write('M10', 'Adjustment Qty', header_cell)
        sheet.write('N10', 'Scrap Qty', header_cell)
        sheet.write('O10', 'Closing Qty', header_cell)

        if based_on == 'product':
            group_by_str = 'PRODUCT_ID'
            if not product_ids:
                product_ids = self.env['product.product'].search([('detailed_type', '=', 'product')])
        else:
            group_by_str = 'CATEGORY_ID'
            if not category_ids:
                category_ids = self.env['product.category'].search([])
            product_ids = self.env['product.product'].search([('categ_id', 'in', category_ids.ids)])

        locations_str = '(' + ', '.join([str(loc.id) for loc in location_ids]) + ')'
        products_str = '(' + ', '.join([str(product.id) for product in product_ids]) + ')'

        query = QUERY.format(group_by_str,
                             locations_str,
                             locations_str,
                             locations_str,
                             locations_str,
                             locations_str,
                             locations_str,
                             locations_str,
                             locations_str,
                             locations_str,
                             locations_str,
                             locations_str,
                             start_date.strftime('%Y-%m-%d %H:%M:%S'),
                             end_date.strftime('%Y-%m-%d %H:%M:%S'),
                             products_str,
                             locations_str,
                             locations_str,
                             start_date.strftime('%Y-%m-%d %H:%M:%S'),
                             end_date.strftime('%Y-%m-%d %H:%M:%S'),
                             products_str,
                             locations_str,
                             group_by_str)

        _logger.info(f'\n{query}\n')
        self.env.cr.execute(query)
        result = self.env.cr.dictfetchall()

        grouped_records = groupby(result, lambda rec: rec['location_id'])
        if based_on == 'product':
            self.group_by_products(workbook, sheet, grouped_records, start_date, location_ids)
        else:
            self.group_by_category(workbook, sheet, grouped_records, start_date)

    def group_by_products(self, workbook, sheet, grouped_records, start_date, allowed_locations):
        row_index = 11
        normal_center_cell = workbook.add_format({
            'font_name': 'Arial', 'font_size': 9, 'border': 1,
            'valign': 'vcenter', 'align': 'center', 'text_wrap': True,
        })
        normal_left_cell = workbook.add_format({
            'font_name': 'Arial', 'font_size': 9, 'border': 1,
            'valign': 'vcenter', 'align': 'left', 'text_wrap': True,
        })
        top_center_cell = workbook.add_format({
            'font_name': 'Arial', 'font_size': 9,
            'valign': 'vcenter', 'align': 'center', 'bold': True,
            'top': 1, 'bottom': 2, 'left': 1, 'right': 1, 'text_wrap': True,
        })
        for location, records in grouped_records:
            number = 1
            location_line_index = row_index
            row_index += 1
            location = self.env['stock.location'].browse(location)
            total_purchase_qty = total_purchase_return_qty = total_sale_qty = total_sale_return_qty = 0
            total_pos_qty = total_pos_return_qty = 0
            total_internal_transfer_qty = total_adjustment_qty = total_scrap_qty = total_opening_qty = total_closing_qty = 0
            if location.id not in allowed_locations.ids:
                continue
            for record in records:
                product = self.env['product.product'].browse(record['product_id'])
                opening_qty = self.env['stock.backdate.report'].with_context(inventory_date=start_date).search([
                    ('product_id', '=', product.id),
                    ('location_id', '=', location.id),
                ]).on_hand_qty
                purchase_qty = record['purchase_qty']
                purchase_return_qty = record['purchase_return_qty']
                sale_qty = record['sale_qty']
                sale_return_qty = record['sale_return_qty']
                pos_qty = record['pos_qty']
                pos_return_qty = record['pos_return_qty']
                internal_transfer_qty = record['internal_transfer_qty']
                adjustment_qty = record['adjustment_qty']
                scrap_qty = record['scrap_qty']
                closing_qty = opening_qty + purchase_qty + purchase_return_qty + sale_qty + sale_return_qty + pos_qty + \
                              pos_return_qty + internal_transfer_qty + adjustment_qty + scrap_qty
                sheet.write(f'A{row_index}', number, normal_center_cell)
                sheet.write(f'B{row_index}', product.name, normal_left_cell)
                sheet.write(f'C{row_index}', product.categ_id.complete_name, normal_center_cell)
                sheet.write(f'D{row_index}', product.default_code, normal_center_cell)
                sheet.write(f'E{row_index}', opening_qty, normal_center_cell)
                sheet.write(f'F{row_index}', purchase_qty, normal_center_cell)
                sheet.write(f'G{row_index}', purchase_return_qty, normal_center_cell)
                sheet.write(f'H{row_index}', sale_qty, normal_center_cell)
                sheet.write(f'I{row_index}', sale_return_qty, normal_center_cell)
                sheet.write(f'J{row_index}', pos_qty, normal_center_cell)
                sheet.write(f'K{row_index}', pos_return_qty, normal_center_cell)
                sheet.write(f'L{row_index}', internal_transfer_qty, normal_center_cell)
                sheet.write(f'M{row_index}', adjustment_qty, normal_center_cell)
                sheet.write(f'N{row_index}', scrap_qty, normal_center_cell)
                sheet.write(f'O{row_index}', closing_qty, normal_center_cell)

                total_opening_qty += opening_qty
                total_purchase_qty += purchase_qty
                total_purchase_return_qty += purchase_return_qty
                total_sale_qty += sale_qty
                total_sale_return_qty += sale_return_qty
                total_pos_qty += pos_qty
                total_pos_return_qty += pos_return_qty
                total_internal_transfer_qty += internal_transfer_qty
                total_adjustment_qty += adjustment_qty
                total_scrap_qty += scrap_qty
                total_closing_qty += closing_qty
                row_index += 1
                number += 1
            sheet.write(f'A{location_line_index}', '', top_center_cell)
            sheet.write(f'B{location_line_index}', location.complete_name, top_center_cell)
            sheet.write(f'C{location_line_index}', '', top_center_cell)
            sheet.write(f'D{location_line_index}', 'Total', top_center_cell)
            sheet.write(f'E{location_line_index}', total_opening_qty, top_center_cell)
            sheet.write(f'F{location_line_index}', total_purchase_qty, top_center_cell)
            sheet.write(f'G{location_line_index}', total_purchase_return_qty, top_center_cell)
            sheet.write(f'H{location_line_index}', total_sale_qty, top_center_cell)
            sheet.write(f'I{location_line_index}', total_sale_return_qty, top_center_cell)
            sheet.write(f'J{location_line_index}', total_pos_qty, top_center_cell)
            sheet.write(f'K{location_line_index}', total_pos_return_qty, top_center_cell)
            sheet.write(f'L{location_line_index}', total_internal_transfer_qty, top_center_cell)
            sheet.write(f'M{location_line_index}', total_adjustment_qty, top_center_cell)
            sheet.write(f'N{location_line_index}', total_scrap_qty, top_center_cell)
            sheet.write(f'O{location_line_index}', total_closing_qty, top_center_cell)
            row_index += 1

    def group_by_category(self, workbook, sheet, grouped_records, start_date):
        row_index = 11
        normal_center_cell = workbook.add_format({
            'font_name': 'Arial', 'font_size': 9, 'border': 1, 'text_wrap': True,
            'valign': 'vcenter', 'align': 'center',
        })
        normal_left_cell = workbook.add_format({
            'font_name': 'Arial', 'font_size': 9, 'border': 1, 'text_wrap': True,
            'valign': 'vcenter', 'align': 'left'
        })
        top_center_cell = workbook.add_format({
            'font_name': 'Arial', 'font_size': 9, 'text_wrap': True,
            'valign': 'vcenter', 'align': 'center', 'bold': True,
            'top': 1, 'bottom': 2, 'left': 1, 'right': 1,
        })
        for location, records in grouped_records:
            number = 1
            location_line_index = row_index
            row_index += 1
            location = self.env['stock.location'].browse(location)
            total_purchase_qty = total_purchase_return_qty = total_sale_qty = total_sale_return_qty = 0
            total_pos_qty = total_pos_return_qty = 0
            total_internal_transfer_qty = total_adjustment_qty = total_scrap_qty = total_opening_qty = total_closing_qty = 0
            for record in records:
                category = self.env['product.category'].browse(record['category_id'])
                opening_qty = sum(self.env['stock.backdate.report'].with_context(inventory_date=start_date).search([
                    ('product_id.categ_id', '=', category.id),
                    ('location_id', '=', location.id),
                ]).mapped('on_hand_qty'))
                purchase_qty = record['purchase_qty']
                purchase_return_qty = record['purchase_return_qty']
                sale_qty = record['sale_qty']
                sale_return_qty = record['sale_return_qty']
                pos_qty = record['pos_qty']
                pos_return_qty = record['pos_return_qty']
                internal_transfer_qty = record['internal_transfer_qty']
                adjustment_qty = record['adjustment_qty']
                scrap_qty = record['scrap_qty']
                closing_qty = opening_qty + purchase_qty + purchase_return_qty + sale_qty + sale_return_qty + pos_qty + pos_return_qty + internal_transfer_qty + adjustment_qty + scrap_qty
                sheet.write(f'A{row_index}', number, normal_center_cell)
                sheet.write(f'B{row_index}', '-', normal_left_cell)
                sheet.write(f'C{row_index}', category.complete_name, normal_left_cell)
                sheet.write(f'D{row_index}', '-', normal_center_cell)
                sheet.write(f'E{row_index}', opening_qty, normal_center_cell)
                sheet.write(f'F{row_index}', purchase_qty, normal_center_cell)
                sheet.write(f'G{row_index}', purchase_return_qty, normal_center_cell)
                sheet.write(f'H{row_index}', sale_qty, normal_center_cell)
                sheet.write(f'I{row_index}', sale_return_qty, normal_center_cell)
                sheet.write(f'J{row_index}', pos_qty, normal_center_cell)
                sheet.write(f'K{row_index}', pos_return_qty, normal_center_cell)
                sheet.write(f'L{row_index}', internal_transfer_qty, normal_center_cell)
                sheet.write(f'M{row_index}', adjustment_qty, normal_center_cell)
                sheet.write(f'N{row_index}', scrap_qty, normal_center_cell)
                sheet.write(f'O{row_index}', closing_qty, normal_center_cell)

                total_opening_qty += opening_qty
                total_purchase_qty += purchase_qty
                total_purchase_return_qty += purchase_return_qty
                total_sale_qty += sale_qty
                total_sale_return_qty += sale_return_qty
                total_pos_qty += pos_qty
                total_pos_return_qty += pos_return_qty
                total_internal_transfer_qty += internal_transfer_qty
                total_adjustment_qty += adjustment_qty
                total_scrap_qty += scrap_qty
                total_closing_qty += closing_qty
                row_index += 1
                number += 1
            sheet.write(f'A{location_line_index}', '', top_center_cell)
            sheet.write(f'B{location_line_index}', location.complete_name, top_center_cell)
            sheet.write(f'C{location_line_index}', '', top_center_cell)
            sheet.write(f'D{location_line_index}', 'Total', top_center_cell)
            sheet.write(f'E{location_line_index}', total_opening_qty, top_center_cell)
            sheet.write(f'F{location_line_index}', total_purchase_qty, top_center_cell)
            sheet.write(f'G{location_line_index}', total_purchase_return_qty, top_center_cell)
            sheet.write(f'H{location_line_index}', total_sale_qty, top_center_cell)
            sheet.write(f'I{location_line_index}', total_sale_return_qty, top_center_cell)
            sheet.write(f'J{location_line_index}', total_pos_qty, top_center_cell)
            sheet.write(f'K{location_line_index}', total_pos_return_qty, top_center_cell)
            sheet.write(f'L{location_line_index}', total_internal_transfer_qty, top_center_cell)
            sheet.write(f'M{location_line_index}', total_adjustment_qty, top_center_cell)
            sheet.write(f'N{location_line_index}', total_scrap_qty, top_center_cell)
            sheet.write(f'O{location_line_index}', total_closing_qty, top_center_cell)
            row_index += 1

        # sheet.set_column(1, 1, None, None, {'hidden': 0})
        # sheet.set_column(3, 3, None, None, {'hidden': 0})
