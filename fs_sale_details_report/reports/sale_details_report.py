from odoo import api, models, fields
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT, DEFAULT_SERVER_DATE_FORMAT
from datetime import datetime
from dateutil.relativedelta import relativedelta


class VanSalesDetailsReportPdf(models.AbstractModel):

    _name = 'report.fs_sale_details_report.sales_details_report_pdf'
    _description = 'Sales Details Report PDF'

    @api.model
    def _get_report_values(self, docids, data=None):
        date_from = data['options']['date_from']
        date_to = data['options']['date_to']
        data['options']['date_from'] = datetime.strptime(date_from, DEFAULT_SERVER_DATE_FORMAT).strftime('%d/%m/%Y')
        data['options']['date_to'] = datetime.strptime(date_to, DEFAULT_SERVER_DATE_FORMAT).strftime('%d/%m/%Y')
        return data


class VanSalesDetailsReportXlsx(models.AbstractModel):

    _name = 'report.fs_sale_details_report.sales_details_report_xlsx'
    _inherit = 'report.report_xlsx.abstract'
    _description = 'Sales Details Report XLSX'

    def generate_xlsx_report(self, workbook, data, docs):
        options = data['options']
        title_style = workbook.add_format({
            'font_name': 'Arial', 'font_size': 11, 'bold': True,
            'valign': 'vcenter', 'align': 'center', 'border': 1,
        })

        header_style = workbook.add_format({
            'font_name': 'Arial', 'font_size': 9, 'bold': True,
            'valign': 'vcenter', 'align': 'center', 'border': 1,
            'num_format': 'mmm-yyyy', 'font_color': '#ffffff', 'bg_color': '#473e8a'
        })

        column_header_left = workbook.add_format({
            'font_name': 'Arial', 'font_size': 9, 'bold': True,
            'valign': 'vcenter', 'align': 'left', 'border': 1,
            'bg_color': '#dad7ed'
        })

        column_header_center = workbook.add_format({
            'font_name': 'Arial', 'font_size': 9, 'bold': True,
            'valign': 'vcenter', 'align': 'center', 'border': 1,
            'bg_color': '#dad7ed'
        })

        normal_cell_style = workbook.add_format({
            'font_name': 'Arial', 'font_size': 9,
            'valign': 'vcenter', 'align': 'center', 'border': 1,
        })

        left_cell_style = workbook.add_format({
            'font_name': 'Arial', 'font_size': 9,
            'valign': 'vcenter', 'align': 'left', 'border': 1,
        })

        date_from = datetime.strptime(options['date_from'], DEFAULT_SERVER_DATE_FORMAT).strftime('%d %B, %Y')
        date_to = datetime.strptime(options['date_to'], DEFAULT_SERVER_DATE_FORMAT).strftime('%d %B, %Y')

        sheet = workbook.add_worksheet('Sale Details Report')

        if options['report_of'] == 'product':
            # Adjust Column Width
            sheet.set_column('E:E', 20)
            sheet.set_column('F:G', 25)

            # Report Title
            sheet.write('E3', 'UOM', header_style)
            sheet.write('F3', 'Price Unit', header_style)
            sheet.write('G3', 'Total', header_style)

            report_of_label = 'Item'
            last_col = 'G'
        else:
            # Adjust Column Width
            sheet.set_column('E:E', 25)

            # Report Title
            sheet.write('E3', 'Total', header_style)

            report_of_label = 'Product Group' if options['report_of'] == 'product_group' else 'Product Category'
            last_col = 'E'

        # Adjust Row Height
        sheet.set_row(0, 30)
        sheet.set_row(1, 25)
        sheet.set_row(2, 22)

        # Adjust Column Width
        sheet.set_column('A:A', 5)
        sheet.set_column('B:B', 10)
        sheet.set_column('C:C', 20)
        sheet.set_column('D:D', 15)

        # Report Title
        sheet.merge_range(f'A1:{last_col}1', 'Sale Details Report', title_style)
        sheet.merge_range(f'A2:{last_col}2', f'{date_from} - {date_to}', title_style)

        # Table Column Headers
        sheet.write('A3', 'No.', header_style)
        sheet.merge_range('B3:C3', report_of_label, header_style)
        sheet.write('D3', 'Qty', header_style)
        row_index = 4
        for record in data['records']:

            sheet.set_row(row_index - 1, 18)
            currency = self.env['res.currency'].browse(record['currency_id'])

            if currency.position == 'before':
                num_format = f'{currency.symbol} #,##0.00'
            else:
                num_format = f'#,##0.00 {currency.symbol}'
            number_cell_style = workbook.add_format({
                'font_name': 'Arial', 'font_size': 9, 'valign': 'vcenter',
                'align': 'right', 'num_format': num_format, 'border': 1,
            })
            column_header_right = workbook.add_format({
                'font_name': 'Arial', 'font_size': 9, 'bold': True,
                'valign': 'vcenter', 'align': 'right', 'border': 1,
                'bg_color': '#dee6ef', 'num_format': num_format
            })

            sheet.merge_range(f'A{row_index}:C{row_index}', record['parent'], column_header_left)
            sheet.write(f'D{row_index}', record['total_qty'], column_header_center)
            if options['report_of'] == 'product':
                sheet.write(f'E{row_index}', '', column_header_center)
                sheet.write(f'F{row_index}', '', column_header_center)
                sheet.write(f'G{row_index}', record['total_amt'], column_header_right)
            else:
                sheet.write(f'E{row_index}', record['total_amt'], column_header_right)
            row_index += 1
            number = 1
            for line in record['lines']:
                line = record['lines'][line]
                sheet.write(f'A{row_index}', number, normal_cell_style)
                sheet.merge_range(f'B{row_index}:C{row_index}', line['report_of_item'], normal_cell_style)
                sheet.write(f'D{row_index}', line['qty'], normal_cell_style)
                if options['report_of'] == 'product':
                    sheet.write(f'E{row_index}', line['uom'], normal_cell_style)
                    sheet.write(f'F{row_index}', line['price_unit'], number_cell_style)
                    sheet.write(f'G{row_index}', line['price_subtotal'], number_cell_style)
                else:
                    sheet.write(f'E{row_index}', line['price_subtotal'], number_cell_style)
                row_index += 1
                number += 1
            row_index += 1


class VanSaleDetailsReport(models.AbstractModel):

    _name = 'van.sale.details.report'
    _description = 'Van Sale Details Report'

    id = fields.Integer('ID')

    def _get_default_report_values(self):
        date = fields.Date.context_today(self)
        date_from = date.replace(day=1).strftime(DEFAULT_SERVER_DATE_FORMAT)
        date_to = (date + relativedelta(day=31)).strftime(DEFAULT_SERVER_DATE_FORMAT)
        team_ids = self.env['crm.team'].search([]).ids
        return date_from, date_to, team_ids, 'sale_team', 'product'

    def _get_sale_teams(self):
        sale_teams = self.env['crm.team'].search([('is_van_team', '=', True),
                                                  ('company_id', '=', self.env.company.id)])
        return sale_teams.ids

    def _get_sale_men(self):
        sale_teams = self.env['crm.team'].search([('is_van_team', '=', True),
                                                  ('company_id', '=', self.env.company.id)])
        return sale_teams.member_ids.ids

    def _get_product_categories(self):
        categories = self.env['product.category'].search([])
        return categories.ids

    @api.model
    def get_data(self, options):
        date_from_str = options.get('date_from', False)
        date_to_str = options.get('date_to', False)
        if not date_from_str or not date_to_str:
            options['date_from'], options['date_to'], options['team_ids'], options['report_by'], options['report_of'] = self._get_default_report_values()
        records, options = self._get_grouped_lines(options)
        return {
            'options': options,
            'records': records,
            'team_ids': self._get_sale_teams(),
            'sale_man_ids': self._get_sale_men(),
            'category_ids': self._get_product_categories(),
        }

    def _get_grouped_lines(self, options):
        data = []
        team_ids = options.get('team_ids', [])
        sale_man_ids = options.get('sale_man_ids', [])
        category_ids = options.get('category_ids', [])
        date_from_str = options.get('date_from')
        date_to_str = options.get('date_to')
        delta = relativedelta(hours=6, minutes=30)
        date_from = (datetime.strptime(date_from_str, DEFAULT_SERVER_DATE_FORMAT) - delta).strftime(DEFAULT_SERVER_DATETIME_FORMAT)
        date_to = (datetime.strptime(date_to_str, DEFAULT_SERVER_DATE_FORMAT) - delta).strftime(DEFAULT_SERVER_DATETIME_FORMAT)
        if options['report_by'] == 'sale_team':
            if not team_ids:
                team_ids = options['team_ids'] = self._get_sale_teams()
            team_ids_str = ','.join([str(team_id) for team_id in team_ids])
            select = 'VO.TEAM_ID, TEAM.NAME AS PARENT,'
            where = f' AND VO.TEAM_ID IN ({team_ids_str}) '
            group_by = order_by = 'VO.TEAM_ID, TEAM.NAME'
        elif options['report_by'] == 'sale_man':
            if not sale_man_ids:
                sale_man_ids = options['sale_man_ids'] = self._get_sale_men()
            sale_man_ids_str = ','.join([str(sale_man_id) for sale_man_id in sale_man_ids])
            select = 'VO.USER_ID, PARTNER.NAME AS PARENT,'
            where = f' AND VO.USER_ID IN ({sale_man_ids_str}) '
            group_by = order_by = 'VO.USER_ID, PARTNER.NAME'
        else:
            if not category_ids:
                category_ids = options['category_ids'] = self._get_product_categories()
            select = 'PC.ID AS CATEGORY_ID, PC.NAME AS PARENT,'
            category_ids_str = ','.join([str(category_id) for category_id in category_ids])
            where = f' AND PC.ID IN ({category_ids_str}) '
            group_by = order_by = 'PC.ID, PC.NAME'
        query = f"""
        SELECT      {select}
                    VO.CURRENCY_ID,
                    SUM(VOL.QTY) AS QTY,
                    SUM(VOL.PRICE_SUBTOTAL) AS TOTAL,
                    JSON_AGG(JSON_BUILD_OBJECT(
                        'product_id', VOL.PRODUCT_ID, 
                        'product', PT.NAME,
                        'qty', QTY,
                        'multi_uom_line_id', VOL.MULTI_UOM_LINE_ID,
                        'uom', UOM.NAME,
                        'currency_id', VO.CURRENCY_ID,
                        'currency_symbol', CUR.SYMBOL,
                        'currency_position', CUR.POSITION,
                        'price_unit', VOL.PRICE_UNIT,
                        'price_subtotal', VOL.PRICE_SUBTOTAL
                    )) AS PRODUCTS

        FROM        VAN_ORDER_LINE VOL
                    LEFT JOIN VAN_ORDER VO ON VO.ID=VOL.ORDER_ID
                    LEFT JOIN PRODUCT_PRODUCT PP ON PP.ID=VOL.PRODUCT_ID
                    LEFT JOIN PRODUCT_TEMPLATE PT ON PT.ID=PP.PRODUCT_TMPL_ID
                    LEFT JOIN PRODUCT_CATEGORY PC ON PC.ID=PT.CATEG_ID
                    LEFT JOIN MULTI_UOM_LINE MUL ON MUL.ID=VOL.MULTI_UOM_LINE_ID
                    LEFT JOIN UOM_UOM UOM ON UOM.ID=MUL.UOM_ID
                    LEFT JOIN RES_CURRENCY CUR ON CUR.ID = VO.CURRENCY_ID
                    LEFT JOIN CRM_TEAM TEAM ON TEAM.ID = VO.TEAM_ID
                    LEFT JOIN RES_USERS US ON US.ID = VO.USER_ID
                    LEFT JOIN RES_PARTNER PARTNER ON PARTNER.ID=US.PARTNER_ID

        WHERE       VO.DATE BETWEEN %s AND %s AND
                    VO.STATE != 'cancel'
                    {where}

        GROUP BY    {group_by}, 
                    VO.CURRENCY_ID
                    
        ORDER BY    {order_by}
        """
        self.env.cr.execute(query, (date_from, date_to))
        records = self.env.cr.dictfetchall()

        for record in records:
            parent = record['parent']
            total_qty = record['qty']
            total_amt = record['total']
            lines = sorted(record['products'], key=lambda l: (l['product'], l['multi_uom_line_id'], l['price_unit']))
            grouped_lines = {}
            for line in lines:
                product_id = line['product_id']
                product_obj = self.env['product.product'].browse(product_id)
                product_group = product_obj.product_group_id
                product_category = product_obj.categ_id
                product = line['product']
                qty = line['qty']
                multi_uom_line_id = line['multi_uom_line_id']
                uom = line['uom']
                currency_id = line['currency_id']
                currency_symbol = line['currency_symbol']
                currency_position = line['currency_position']
                price_unit = round(line['price_unit'], 2)
                price_subtotal = round(line['price_subtotal'], 2)
                if options['report_of'] == 'product':
                    key = f'{product_id}, {multi_uom_line_id}, {price_unit}, {currency_id}'
                    report_of_item = product
                elif options['report_of'] == 'product_group':
                    key = f'product_group_{product_group.id}'
                    report_of_item = product_group.name
                else:
                    key = f'product_category_{product_category.id}'
                    report_of_item = product_category.display_name
                existing_line = grouped_lines.get(key, False)
                if existing_line:
                    qty += existing_line['qty']
                    price_subtotal += existing_line['price_subtotal']
                formatted_price_unit = "{:,.2f}".format(price_unit)
                formatted_price_subtotal = "{:,.2f}".format(price_subtotal)
                if currency_position == 'before':
                    price_unit_display = f'{currency_symbol} {formatted_price_unit}'
                    price_subtotal_display = f'{currency_symbol} {formatted_price_subtotal}'
                else:
                    price_unit_display = f'{formatted_price_unit} {currency_symbol}'
                    price_subtotal_display = f'{formatted_price_subtotal} {currency_symbol}'
                line_vals = {
                    'report_of_item': report_of_item,
                    'qty': qty,
                    'uom': uom,
                    'price_unit_display': price_unit_display,
                    'price_subtotal_display': price_subtotal_display,
                    'price_unit': price_unit,
                    'price_subtotal': price_subtotal,
                }
                grouped_lines[key] = line_vals
            currency = self.env['res.currency'].browse(record['currency_id'])
            formatted_total_amt = "{:,.2f}".format(total_amt)
            if currency.position == 'before':
                total_amt_display = f'{currency.symbol} {formatted_total_amt}'
            else:
                total_amt_display = f'{formatted_total_amt} {currency.symbol}'
            data.append({
                'parent': parent,
                'lines': grouped_lines,
                'currency_id': currency.id,
                'total_qty': total_qty,
                'total_amt': total_amt,
                'total_amt_display': total_amt_display,
            })
        return data, options

    @api.model
    def download_report(self, report_type, data):
        if report_type == 'xlsx':
            xml_id = 'fs_sale_details_report.sale_details_report_xlsx'
        else:
            xml_id = 'fs_sale_details_report.sale_details_report_pdf'
        return self.env.ref(xml_id).report_action([1], data=data)
