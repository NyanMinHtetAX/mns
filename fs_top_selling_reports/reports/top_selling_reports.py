import logging
from odoo import api, models, fields
from datetime import datetime
from dateutil.relativedelta import relativedelta
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT, DEFAULT_SERVER_DATE_FORMAT


_logger = logging.getLogger(__name__)

report_information = {
    'sale_team': {
        'title': 'Top Selling Report by Sales Team',
        'column_headers': [
            ('A', 'No.'),
            ('B', 'Sales Team'),
            ('C', 'Invoicing Target'),
            ('D', 'Total Sale Amount'),
        ],
        'last_column': 'D',
        'record_structure': [
            ('B', 'name'),
            ('C', 'invoiced_target'),
            ('D', 'total'),
        ],
    },
    'customer': {
        'title': 'Top Selling Report by Customer',
        'column_headers': [
            ('A', 'No.'),
            ('B', 'Customer Code'),
            ('C', 'Customer Name'),
            ('D', 'Total Sale Amount'),
        ],
        'last_column': 'D',
        'record_structure': [
            ('B', 'ref'),
            ('C', 'name'),
            ('D', 'total'),
        ],
    },
    'salesman': {
        'title': 'Top Selling Report by Salesman',
        'column_headers': [
            ('A', 'No.'),
            ('B', 'Salesman'),
            ('C', 'Sales Team'),
            ('D', 'Total Sale Amount'),
        ],
        'last_column': 'D',
        'record_structure': [
            ('B', 'name'),
            ('C', 'team'),
            ('D', 'total'),
        ],
    },
    'product': {
        'title': 'Top Selling Report by Product',
        'column_headers': [
            ('A', 'No.'),
            ('B', 'Code'),
            ('C', 'Item'),
            ('D', 'Qty'),
            ('E', 'UoM'),
        ],
        'last_column': 'E',
        'record_structure': [
            ('B', 'code'),
            ('C', 'name'),
            ('D', 'qty'),
            ('E', 'uom'),
        ],
    },
}


class TopSellingReportXLSX(models.AbstractModel):

    _name = 'report.fs_top_selling_reports.fs_top_selling_reports_xlsx'
    _inherit = 'report.report_xlsx.abstract'
    _description = 'Top Selling Report - XLSX'

    def generate_xlsx_report(self, workbook, data, docs):
        title_style = workbook.add_format({
            'font_name': 'Arial', 'font_size': 11, 'bold': True,
            'valign': 'vcenter', 'align': 'center',
        })

        header_style = workbook.add_format({
            'font_name': 'Arial', 'font_size': 9, 'bold': True,
            'valign': 'vcenter', 'align': 'center', 'border': 1,
            'num_format': 'mmm-yyyy', 'font_color': '#ffffff', 'bg_color': '#473e8a'
        })

        normal_cell_style = workbook.add_format({
            'font_name': 'Arial', 'font_size': 9,
            'valign': 'vcenter', 'align': 'center', 'border': 1,
        })

        sheet = workbook.add_worksheet('Top Selling Report')

        report_info = report_information[data['options']['report_by']]
        column_headers = report_info['column_headers']
        last_column = report_info['last_column']
        record_structure = report_info['record_structure']

        # Adjust Row Height
        sheet.set_row(0, 25)
        sheet.set_row(1, 25)
        sheet.set_row(2, 25)

        # Adjust Column Width
        sheet.set_column('A:A', 5)
        sheet.set_column('B:B', 25)
        sheet.set_column('C:C', 20)
        sheet.set_column('D:D', 20)

        # Report Title
        date_from = datetime.strptime(data['options']['date_from'], DEFAULT_SERVER_DATE_FORMAT).strftime('%d %B, %Y')
        date_to = datetime.strptime(data['options']['date_to'], DEFAULT_SERVER_DATE_FORMAT).strftime('%d %B, %Y')
        sheet.merge_range(f'A1:{last_column}1', report_info['title'], title_style)
        sheet.merge_range(f'A2:{last_column}2', f'{date_from} - {date_to}', title_style)

        # Table Column Headers
        for column_header in column_headers:
            sheet.write(f'{column_header[0]}3', column_header[1], header_style)

        row_index = 4
        number = 1
        for record in data['records']:
            sheet.write(f'A{row_index}', number, normal_cell_style)
            for column in record_structure:
                sheet.write(f'{column[0]}{row_index}', record[column[1]],  normal_cell_style)
            number += 1
            row_index += 1


class TopSellingReport(models.AbstractModel):

    _name = 'top.selling.report'
    _description = 'Top Selling Report'

    id = fields.Integer('ID')

    @api.model
    def get_data(self, options):
        root_select = options['root_select']
        root_group_by = options['root_group_by']
        select = options['select']
        group_by = options['group_by']
        order_by = options['order_by']
        date_from_str = options['date_from']
        date_to_str = options['date_to']
        delta = relativedelta(hours=6, minutes=30)
        date_from = (datetime.strptime(date_from_str, DEFAULT_SERVER_DATE_FORMAT) - delta).strftime(DEFAULT_SERVER_DATETIME_FORMAT)
        date_to = (datetime.strptime(date_to_str, DEFAULT_SERVER_DATE_FORMAT) - delta).strftime(DEFAULT_SERVER_DATETIME_FORMAT)
        company = self.env.company
        company_currency = company.currency_id
        query = f"""
        SELECT      {root_select}, SUM(QTY) AS QTY, SUM(TOTAL) AS TOTAL
        
        FROM
        (
        SELECT      {select},
                    SUM(VOL.QTY) AS QTY, 
                    SUM(
                        CASE
                            WHEN VO.CURRENCY_ID={company_currency.id} THEN VOL.PRICE_SUBTOTAL
                            ELSE ROUND(
                                VOL.PRICE_SUBTOTAL /
                                COALESCE((
                                        SELECT      R.RATE FROM RES_CURRENCY_RATE R
                                        WHERE       R.CURRENCY_ID = VO.CURRENCY_ID AND R.NAME <= VO.DATE
                                                    AND (R.COMPANY_ID IS NULL OR R.COMPANY_ID = {company.id})
                                        ORDER BY    R.COMPANY_ID, R.NAME DESC
                                        LIMIT 1
                                    ), 1.0
                                )
                            , 2)
                        END
                    ) AS TOTAL
        
        FROM        VAN_ORDER_LINE VOL    
                    LEFT JOIN VAN_ORDER VO ON VO.ID=VOL.ORDER_ID
                    LEFT JOIN PRODUCT_PRODUCT PP ON PP.ID=VOL.PRODUCT_ID
                    LEFT JOIN PRODUCT_TEMPLATE PT ON PT.ID=PP.PRODUCT_TMPL_ID
                    LEFT JOIN UOM_UOM UOM ON UOM.ID=PT.UOM_ID
                    LEFT JOIN PRODUCT_CATEGORY PC ON PC.ID=PT.CATEG_ID
                    LEFT JOIN CRM_TEAM ST ON ST.ID=VO.TEAM_ID
                    LEFT JOIN RES_USERS US ON US.ID=VO.USER_ID
                    LEFT JOIN RES_PARTNER RP ON RP.ID=US.PARTNER_ID
                    LEFT JOIN RES_PARTNER CUSTOMER ON CUSTOMER.ID=VO.PARTNER_ID
        
        WHERE       VO.DATE BETWEEN '{date_from}' AND '{date_to}' AND
                    VO.STATE != 'cancel' AND
                    VO.COMPANY_ID={company.id}
                    
        GROUP BY    {group_by}
        
        UNION ALL
        
        SELECT      {select},
                    SUM(SOL.PRODUCT_UOM_QTY) AS QTY, 
                    SUM(
                        CASE
                            WHEN SO.CURRENCY_ID={company_currency.id} THEN SOL.PRICE_SUBTOTAL
                            ELSE ROUND(
                                SOL.PRICE_SUBTOTAL /
                                COALESCE((
                                        SELECT      R.RATE FROM RES_CURRENCY_RATE R
                                        WHERE       R.CURRENCY_ID = SO.CURRENCY_ID AND R.NAME <= SO.DATE_ORDER
                                                    AND (R.COMPANY_ID IS NULL OR R.COMPANY_ID = {company.id})
                                        ORDER BY    R.COMPANY_ID, R.NAME DESC
                                        LIMIT 1
                                    ), 1.0
                                )
                            , 2)
                        END
                    ) AS TOTAL
        
        FROM        SALE_ORDER_LINE SOL    
                    LEFT JOIN SALE_ORDER SO ON SO.ID=SOL.ORDER_ID
                    LEFT JOIN PRODUCT_PRODUCT PP ON PP.ID=SOL.PRODUCT_ID
                    LEFT JOIN PRODUCT_TEMPLATE PT ON PT.ID=PP.PRODUCT_TMPL_ID
                    LEFT JOIN UOM_UOM UOM ON UOM.ID=PT.UOM_ID
                    LEFT JOIN PRODUCT_CATEGORY PC ON PC.ID=PT.CATEG_ID
                    LEFT JOIN CRM_TEAM ST ON ST.ID=SO.TEAM_ID
                    LEFT JOIN RES_USERS US ON US.ID=SO.USER_ID
                    LEFT JOIN RES_PARTNER RP ON RP.ID=US.PARTNER_ID
                    LEFT JOIN RES_PARTNER CUSTOMER ON CUSTOMER.ID=SO.PARTNER_ID
        
        WHERE       SO.DATE_ORDER BETWEEN '{date_from}' AND '{date_to}' AND
                    SO.STATE != 'cancel' AND SO.SALE_TYPE='pre_order' AND
                    SO.COMPANY_ID={company.id}
                    
        GROUP BY    {group_by}     
        
        ) AS TR   
        
        GROUP BY    {root_group_by}
        """
        _logger.info(f'\n\n\nExecuting the query for top selling report------\n')
        _logger.info(f'\n{query}\n')
        self.env.cr.execute(query)
        records = self.env.cr.dictfetchall()
        records = sorted(records, key=lambda rec: rec[order_by], reverse=True)
        if company_currency.position == 'before':
            currency_before = company_currency.symbol
            currency_after = ''
        else:
            currency_before = ''
            currency_after = company_currency.symbol
        return {
            'options': options,
            'records': records,
            'currency_before': currency_before,
            'currency_after': currency_after,
        }

    @api.model
    def download_report(self, report_type, data):
        xml_id = f'fs_top_selling_reports.fs_top_selling_report_{report_type}'
        date_from = datetime.strptime(data['options']['date_from'], DEFAULT_SERVER_DATE_FORMAT).strftime('%d-%m-%Y')
        date_to = datetime.strptime(data['options']['date_to'], DEFAULT_SERVER_DATE_FORMAT).strftime('%d-%m-%Y')
        data['options']['date_from'] = date_from
        data['options']['date_to'] = date_to
        return self.env.ref(xml_id).report_action(docids=[], data=data)
