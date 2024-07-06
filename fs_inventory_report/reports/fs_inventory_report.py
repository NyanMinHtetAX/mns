import logging
from itertools import groupby
from odoo import api, models, fields
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT, DEFAULT_SERVER_DATE_FORMAT
from datetime import datetime
from odoo.exceptions import UserError
from dateutil.relativedelta import relativedelta

_logger = logging.getLogger(__name__)


class FsInventoryReportXLSX(models.AbstractModel):
    _name = 'report.fs_inventory_report.fs_inventory_report_xlsx'
    _inherit = 'report.report_xlsx.abstract'
    _description = 'FS Inventory Report - XLSX'

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

        sale_team_cell_style = workbook.add_format({
            'font_name': 'Arial', 'font_size': 9, 'bg_color': '#dad7ed',
            'valign': 'vcenter', 'align': 'center', 'border': 1, 'bold': True
        })

        normal_cell_style = workbook.add_format({
            'font_name': 'Arial', 'font_size': 9,
            'valign': 'vcenter', 'align': 'center', 'border': 1,
        })

        sheet = workbook.add_worksheet('Inventory Report')

        # Adjust Row Height
        sheet.set_row(0, 25)
        sheet.set_row(1, 25)
        sheet.set_row(2, 25)

        # Adjust Column Width
        sheet.set_column('A:A', 5)
        sheet.set_column('B:B', 15)
        sheet.set_column('C:C', 30)
        sheet.set_column('D:N', 10)

        # Report Title
        date = datetime.strptime(data['options']['date'], DEFAULT_SERVER_DATETIME_FORMAT).strftime('%d %B, %Y')
        sheet.merge_range('A1:N1', 'Inventory Report', title_style)
        sheet.merge_range('A2:N2', date, title_style)
        sheet.merge_range('A3:N3', ', '.join([team['name'] for team in data['teams']]), title_style)

        # Table Column Headers
        sheet.merge_range('A4:A5', 'No.', header_style)
        sheet.merge_range('B4:B5', 'Code', header_style)
        sheet.merge_range('C4:C5', 'Item', header_style)
        sheet.merge_range('D4:E4', 'Opening', header_style)
        sheet.merge_range('F4:G4', 'Sale', header_style)
        sheet.merge_range('H4:I4', 'Sale Return', header_style)
        sheet.write('J4', 'Transfer', header_style)
        sheet.merge_range('K4:L4', 'Scrap', header_style)
        sheet.merge_range('M4:N4', 'Closing', header_style)
        sheet.write('D5', 'Qty', header_style)
        sheet.write('E5', 'Value', header_style)
        sheet.write('F5', 'Qty', header_style)
        sheet.write('G5', 'Value', header_style)
        sheet.write('H5', 'Qty', header_style)
        sheet.write('I5', 'Value', header_style)
        sheet.write('J5', 'Qty', header_style)
        sheet.write('K5', 'Qty', header_style)
        sheet.write('L5', 'Value', header_style)
        sheet.write('M5', 'Qty', header_style)
        sheet.write('N5', 'Value', header_style)

        row_index = 6
        transactions = data['transactions']
        for team in data['teams']:
            number = 1

            record = transactions.get(str(team['location_id']), {})
            sheet.merge_range(f'A{row_index}:C{row_index}', f'{team["name"]} - {team["location"]}',
                              sale_team_cell_style)
            sheet.write(f'D{row_index}', record.get('opening_qty'), sale_team_cell_style)
            sheet.write(f'E{row_index}', record.get('opening_value'), sale_team_cell_style)
            sheet.write(f'F{row_index}', record.get('sale_qty'), sale_team_cell_style)
            sheet.write(f'G{row_index}', record.get('sale_value'), sale_team_cell_style)
            sheet.write(f'H{row_index}', record.get('sale_return_qty'), sale_team_cell_style)
            sheet.write(f'I{row_index}', record.get('sale_return_value'), sale_team_cell_style)
            sheet.write(f'J{row_index}', record.get('transfer_qty'), sale_team_cell_style)
            sheet.write(f'K{row_index}', record.get('scrap_qty'), sale_team_cell_style)
            sheet.write(f'L{row_index}', record.get('scrap_value'), sale_team_cell_style)
            sheet.write(f'M{row_index}', record.get('closing_qty'), sale_team_cell_style)
            sheet.write(f'N{row_index}', record.get('closing_value'), sale_team_cell_style)
            row_index += 1
            for line in record.get('lines', []):
                sheet.write(f'A{row_index}', number, normal_cell_style)
                sheet.write(f'B{row_index}', line.get('code'), normal_cell_style)
                sheet.write(f'C{row_index}', line.get('product'), normal_cell_style)
                sheet.write(f'D{row_index}', line.get('opening_qty'), normal_cell_style)
                sheet.write(f'E{row_index}', line.get('opening_value'), normal_cell_style)
                sheet.write(f'F{row_index}', line.get('sale_qty'), normal_cell_style)
                sheet.write(f'G{row_index}', line.get('sale_value'), normal_cell_style)
                sheet.write(f'H{row_index}', line.get('sale_return_qty'), normal_cell_style)
                sheet.write(f'I{row_index}', line.get('sale_return_value'), normal_cell_style)
                sheet.write(f'J{row_index}', line.get('transfer_qty'), normal_cell_style)
                sheet.write(f'K{row_index}', line.get('scrap_qty'), normal_cell_style)
                sheet.write(f'L{row_index}', line.get('scrap_value'), normal_cell_style)
                sheet.write(f'M{row_index}', line.get('closing_qty'), normal_cell_style)
                sheet.write(f'N{row_index}', line.get('closing_value'), normal_cell_style)
                number += 1
                row_index += 1


class FsInventoryReport(models.AbstractModel):
    _name = 'fs.inventory.report'
    _description = 'Field Sale Inventory Report'

    id = fields.Integer('ID')

    @api.model
    def get_data(self, options):
        # import pdb
        # pdb.set_trace()

        company = self.env.company
        start_time = datetime.strptime(options['date'], DEFAULT_SERVER_DATETIME_FORMAT).date() - relativedelta(hours=6, minutes=30)
        end_time = start_time + relativedelta(days=1, seconds=-1)

        if options.get('team_ids', []):
            team_ids = options['team_ids']
        else:
            team_ids = options['team_ids'] or self.env['crm.team'].search([('is_van_team', '=', True)]).ids
        teams = self.env['crm.team'].browse(team_ids)
        if not teams:
            raise UserError('Sale team is not yet create. Please create at least one sale team')

        location_ids = teams.van_location_id
        location_dest_ids = teams.allowed_location_ids.ids
        locations_str = '(' + ','.join([str(loc.id) for loc in location_ids]) + ')'
        location_dest_str = '(' + ','.join([str(loc) for loc in location_dest_ids]) + ')'
        query = f"""   
        SELECT      CODE,
                    PRODUCT,
                    TR.PRODUCT_ID,
                    TR.LOCATION_ID,
                    COALESCE(OP.QTY, 0.0) AS OPENING_QTY,
                    COALESCE(OP.VALUE, 0.0) AS OPENING_VALUE,
                    SUM(SALE_QTY) AS SALE_QTY,
                    SUM(SALE_VALUE) AS SALE_VALUE,
                    SUM(SALE_RETURN_QTY) AS SALE_RETURN_QTY,
                    SUM(SALE_RETURN_VALUE) AS SALE_RETURN_VALUE,
                    SUM(TRANSFER_QTY) AS TRANSFER_QTY,
                    SUM(SCRAP_QTY) AS SCRAP_QTY,
                    SUM(SCRAP_VALUE) AS SCRAP_VALUE,
                    COALESCE(CL.QTY, 0.0) AS CLOSING_QTY,
                    COALESCE(CL.VALUE, 0.0) AS CLOSING_VALUE
        
        FROM (
        SELECT      SML.PRODUCT_ID,
                    PT.NAME AS PRODUCT,
                    PP.DEFAULT_CODE AS CODE,
                    SML.LOCATION_ID,
                    CASE
                        WHEN SM.VAN_ORDER_LINE_ID IS NOT NULL OR (SM.SALE_LINE_ID IS NOT NULL AND SO.SALE_TYPE = 'pre_order') 
                        THEN -SML.QTY_DONE
                        ELSE 0
                    END AS SALE_QTY,
                    CASE
                        WHEN SM.VAN_ORDER_LINE_ID IS NOT NULL OR (SM.SALE_LINE_ID IS NOT NULL AND SO.SALE_TYPE = 'pre_order') 
                        THEN (SELECT COALESCE(SUM(-UNIT_COST * SML.QTY_DONE), 0) FROM STOCK_VALUATION_LAYER WHERE STOCK_MOVE_ID=SM.ID)
                        ELSE 0
                    END AS SALE_VALUE,
                    0 SALE_RETURN_QTY,
                    0 SALE_RETURN_VALUE,
                    CASE 
                        WHEN DL.USAGE='internal' THEN -SML.QTY_DONE
                        ELSE 0
                    END AS TRANSFER_QTY,
                    CASE
                        WHEN SCRAP.ID IS NOT NULL
                        THEN -SML.QTY_DONE
                        ELSE 0
                    END AS SCRAP_QTY,
                    CASE
                        WHEN SCRAP.ID IS NOT NULL
                        THEN (SELECT COALESCE(SUM(-UNIT_COST * SML.QTY_DONE), 0) FROM STOCK_VALUATION_LAYER WHERE STOCK_MOVE_ID=SM.ID)
                        ELSE 0
                    END AS SCRAP_VALUE
        
        FROM        STOCK_MOVE_LINE SML
                    LEFT JOIN STOCK_MOVE SM ON SM.ID=SML.MOVE_ID
                    LEFT JOIN STOCK_LOCATION SL ON SL.ID=SML.LOCATION_ID
                    LEFT JOIN STOCK_LOCATION DL ON DL.ID=SML.LOCATION_DEST_ID
                    LEFT JOIN PRODUCT_PRODUCT PP ON PP.ID=SML.PRODUCT_ID
                    LEFT JOIN PRODUCT_TEMPLATE PT ON PT.ID=PP.PRODUCT_TMPL_ID
                    LEFT JOIN SALE_ORDER_LINE SOL ON SOL.ID=SM.SALE_LINE_ID
                    LEFT JOIN SALE_ORDER SO ON SO.ID=SOL.ORDER_ID
                    LEFT JOIN STOCK_MULTI_SCRAP_LINE SCRAP ON SM.ID=SCRAP.MOVE_ID
                    LEFT JOIN RES_COMPANY COMPANY ON COMPANY.ID=SM.COMPANY_ID
                    
        WHERE       SML.STATE='done' AND SL.ID IN {locations_str} AND COMPANY.ID={company.id}
                    AND SML.DATE >='{start_time}' AND SML.DATE <= '{end_time}'  
        UNION ALL
        SELECT      SML.PRODUCT_ID,
                    PT.NAME AS PRODUCT,
                    PP.DEFAULT_CODE AS CODE,
                    SML.LOCATION_DEST_ID AS LOCATION_ID,
                    0 SALE_QTY,
                    0 SALE_VALUE,
                    CASE
                        WHEN SM.VAN_ORDER_LINE_ID IS NOT NULL OR (SM.SALE_LINE_ID IS NOT NULL AND SO.SALE_TYPE = 'pre_order') 
                        THEN SML.QTY_DONE
                        ELSE 0
                    END AS SALE_RETURN_QTY,
                    CASE
                        WHEN SM.VAN_ORDER_LINE_ID IS NOT NULL OR (SM.SALE_LINE_ID IS NOT NULL AND SO.SALE_TYPE = 'pre_order') 
                        THEN (SELECT COALESCE(SUM(UNIT_COST * SML.QTY_DONE), 0) FROM STOCK_VALUATION_LAYER WHERE STOCK_MOVE_ID=SM.ID)
                        ELSE 0
                    END AS SALE_RETURN_VALUE,
                    CASE 
                        WHEN SL.USAGE='internal' THEN SML.QTY_DONE
                        ELSE 0
                    END AS TRANSFER_QTY,
                    CASE
                        WHEN SCRAP.ID IS NOT NULL
                        THEN SML.QTY_DONE
                        ELSE 0
                    END AS SCRAP_QTY,
                    CASE
                        WHEN SCRAP.ID IS NOT NULL
                        THEN (SELECT COALESCE(SUM(UNIT_COST * SML.QTY_DONE), 0) FROM STOCK_VALUATION_LAYER WHERE STOCK_MOVE_ID=SM.ID)
                        ELSE 0
                    END AS SCRAP_VALUE
        
        FROM        STOCK_MOVE_LINE SML
                    LEFT JOIN STOCK_MOVE SM ON SM.ID=SML.MOVE_ID
                    LEFT JOIN STOCK_LOCATION SL ON SL.ID=SML.LOCATION_ID
                    LEFT JOIN STOCK_LOCATION DL ON DL.ID=SML.LOCATION_DEST_ID
                    LEFT JOIN PRODUCT_PRODUCT PP ON PP.ID=SML.PRODUCT_ID
                    LEFT JOIN PRODUCT_TEMPLATE PT ON PT.ID=PP.PRODUCT_TMPL_ID
                    LEFT JOIN STOCK_MULTI_SCRAP_LINE SCRAP ON SM.ID=SCRAP.MOVE_ID
                    LEFT JOIN SALE_ORDER_LINE SOL ON SOL.ID=SM.SALE_LINE_ID
                    LEFT JOIN SALE_ORDER SO ON SO.ID=SOL.ORDER_ID
                    LEFT JOIN RES_COMPANY COMPANY ON COMPANY.ID=SM.COMPANY_ID
                    
        WHERE       SML.STATE='done' AND DL.ID IN {locations_str} AND COMPANY.ID={company.id}
                    AND SML.DATE >='{start_time}' AND SML.DATE <= '{end_time}'
        ) AS TR
        
        LEFT JOIN (
            SELECT      PRODUCT_ID, 
                        LOCATION_ID, 
                        ROUND(CAST(SUM(QTY) AS NUMERIC), 2) AS QTY,
                        ROUND(CAST(SUM(VALUE) AS NUMERIC), 2) AS VALUE
            FROM 
            (
            SELECT      SML.PRODUCT_ID,
                        SML.LOCATION_ID,
                        SUM(
                            -SML.QTY_DONE / NULLIF(COALESCE(LINE_UOM.FACTOR, 1) / COALESCE(PRODUCT_UOM.FACTOR, 1), 0.0)
                        ) AS QTY,
                        CASE
                            WHEN DL.USAGE = 'internal' 
                            THEN (-SML.QTY_DONE / NULLIF(COALESCE(LINE_UOM.FACTOR, 1) / COALESCE(PRODUCT_UOM.FACTOR, 1), 0.0)) * COALESCE(IP.VALUE_FLOAT, 0)
                            ELSE
                            SUM(
                                (SELECT SUM(VALUE) FROM STOCK_VALUATION_LAYER WHERE STOCK_MOVE_ID=SM.ID)
                            )
                        END AS VALUE
            FROM        STOCK_MOVE_LINE SML
                        LEFT JOIN STOCK_MOVE SM ON SM.ID=SML.MOVE_ID
                        LEFT JOIN PRODUCT_PRODUCT PP ON PP.ID=SML.PRODUCT_ID
                        LEFT JOIN PRODUCT_TEMPLATE PT ON PT.ID=PP.PRODUCT_TMPL_ID
                        LEFT JOIN IR_PROPERTY IP ON (IP.RES_ID=('product.product,' || PP.ID) AND IP.NAME='standard_price' AND IP.COMPANY_ID={company.id})
                        LEFT JOIN STOCK_LOCATION SL ON SL.ID=SML.LOCATION_ID
                        LEFT JOIN STOCK_LOCATION DL ON DL.ID=SML.LOCATION_DEST_ID
                        LEFT JOIN UOM_UOM PRODUCT_UOM ON PRODUCT_UOM.ID=PT.UOM_ID
                        LEFT JOIN UOM_UOM LINE_UOM ON LINE_UOM.ID=SML.PRODUCT_UOM_ID
            WHERE       SML.DATE <= '{start_time}' AND SL.USAGE='internal' AND SM.COMPANY_ID={company.id}
            GROUP BY    SML.ID, SML.PRODUCT_ID, PT.DEFAULT_CODE, SML.LOCATION_ID, PT.UOM_ID, DL.USAGE, LINE_UOM.FACTOR, PRODUCT_UOM.FACTOR, IP.VALUE_FLOAT
            
            UNION ALL
            
            SELECT      SML.PRODUCT_ID,
                        SML.LOCATION_DEST_ID AS LOCATION_ID,
                        SUM(
                            SML.QTY_DONE / NULLIF(COALESCE(LINE_UOM.FACTOR, 1) / COALESCE(PRODUCT_UOM.FACTOR, 1), 0.0)
                        ) AS QTY,
                        CASE
                            WHEN SL.USAGE = 'internal' 
                            THEN (SML.QTY_DONE / NULLIF(COALESCE(LINE_UOM.FACTOR, 1) / COALESCE(PRODUCT_UOM.FACTOR, 1), 0.0)) * COALESCE(IP.VALUE_FLOAT, 0)
                            ELSE
                            SUM(
                                (SELECT SUM(VALUE) FROM STOCK_VALUATION_LAYER WHERE STOCK_MOVE_ID=SM.ID)
                            )
                        END AS VALUE
            FROM        STOCK_MOVE_LINE SML
                        LEFT JOIN STOCK_MOVE SM ON SM.ID=SML.MOVE_ID
                        LEFT JOIN PRODUCT_PRODUCT PP ON PP.ID=SML.PRODUCT_ID
                        LEFT JOIN PRODUCT_TEMPLATE PT ON PT.ID=PP.PRODUCT_TMPL_ID
                        LEFT JOIN IR_PROPERTY IP ON (IP.RES_ID=('product.product,' || PP.ID) AND IP.NAME='standard_price' AND IP.COMPANY_ID={company.id})
                        LEFT JOIN STOCK_LOCATION SL ON SL.ID=SML.LOCATION_DEST_ID
                        LEFT JOIN STOCK_LOCATION DL ON DL.ID=SML.LOCATION_ID
                        LEFT JOIN UOM_UOM PRODUCT_UOM ON PRODUCT_UOM.ID=PT.UOM_ID
                        LEFT JOIN UOM_UOM LINE_UOM ON LINE_UOM.ID=SML.PRODUCT_UOM_ID
            WHERE       SML.DATE <= '{end_time}' AND DL.USAGE='internal' AND SM.COMPANY_ID={company.id} 
            GROUP BY    SML.ID, SML.PRODUCT_ID, PT.DEFAULT_CODE, SML.LOCATION_DEST_ID, PT.UOM_ID, SL.USAGE, LINE_UOM.FACTOR, PRODUCT_UOM.FACTOR, IP.VALUE_FLOAT
            ) AS OPENING  
            GROUP BY    PRODUCT_ID, LOCATION_ID
        ) OP ON (OP.PRODUCT_ID=TR.PRODUCT_ID AND OP.LOCATION_ID=TR.LOCATION_ID)
                
        LEFT JOIN (
            SELECT      PRODUCT_ID, 
                        LOCATION_ID, 
                        ROUND(CAST(SUM(QTY) AS NUMERIC), 2) AS QTY,
                        ROUND(CAST(SUM(VALUE) AS NUMERIC), 2) AS VALUE
            FROM 
            (
            SELECT      SML.PRODUCT_ID,
                        SML.LOCATION_ID,
                        SUM(
                            -SML.QTY_DONE / NULLIF(COALESCE(LINE_UOM.FACTOR, 1) / COALESCE(PRODUCT_UOM.FACTOR, 1), 0.0)
                        ) AS QTY,
                        CASE
                            WHEN DL.USAGE = 'internal' 
                            THEN (-SML.QTY_DONE / NULLIF(COALESCE(LINE_UOM.FACTOR, 1) / COALESCE(PRODUCT_UOM.FACTOR, 1), 0.0)) * COALESCE(IP.VALUE_FLOAT, 0)
                            ELSE
                            SUM(
                                (SELECT SUM(VALUE) FROM STOCK_VALUATION_LAYER WHERE STOCK_MOVE_ID=SM.ID)
                            )
                        END AS VALUE
            FROM        STOCK_MOVE_LINE SML
                        LEFT JOIN STOCK_MOVE SM ON SM.ID=SML.MOVE_ID
                        LEFT JOIN PRODUCT_PRODUCT PP ON PP.ID=SML.PRODUCT_ID
                        LEFT JOIN PRODUCT_TEMPLATE PT ON PT.ID=PP.PRODUCT_TMPL_ID
                        LEFT JOIN IR_PROPERTY IP ON (IP.RES_ID=('product.product,' || PP.ID) AND IP.NAME='standard_price' AND IP.COMPANY_ID={company.id})
                        LEFT JOIN STOCK_LOCATION SL ON SL.ID=SML.LOCATION_ID
                        LEFT JOIN STOCK_LOCATION DL ON DL.ID=SML.LOCATION_DEST_ID
                        LEFT JOIN UOM_UOM PRODUCT_UOM ON PRODUCT_UOM.ID=PT.UOM_ID
                        LEFT JOIN UOM_UOM LINE_UOM ON LINE_UOM.ID=SML.PRODUCT_UOM_ID
            WHERE       SML.DATE <= '{end_time}' AND SL.USAGE='internal' AND SM.COMPANY_ID={company.id}
            GROUP BY    SML.ID, SML.PRODUCT_ID, PT.DEFAULT_CODE, SML.LOCATION_ID, PT.UOM_ID, DL.USAGE, LINE_UOM.FACTOR, PRODUCT_UOM.FACTOR, IP.VALUE_FLOAT
            
            UNION ALL
            
            SELECT      SML.PRODUCT_ID,
                        SML.LOCATION_DEST_ID AS LOCATION_ID,
                        SUM(
                            SML.QTY_DONE / NULLIF(COALESCE(LINE_UOM.FACTOR, 1) / COALESCE(PRODUCT_UOM.FACTOR, 1), 0.0)
                        ) AS QTY,
                        CASE
                            WHEN SL.USAGE = 'internal' 
                            THEN (SML.QTY_DONE / NULLIF(COALESCE(LINE_UOM.FACTOR, 1) / COALESCE(PRODUCT_UOM.FACTOR, 1), 0.0)) * COALESCE(IP.VALUE_FLOAT, 0)
                            ELSE
                            SUM(
                                (SELECT SUM(VALUE) FROM STOCK_VALUATION_LAYER WHERE STOCK_MOVE_ID=SM.ID)
                            )
                        END AS VALUE
            FROM        STOCK_MOVE_LINE SML
                        LEFT JOIN STOCK_MOVE SM ON SM.ID=SML.MOVE_ID
                        LEFT JOIN PRODUCT_PRODUCT PP ON PP.ID=SML.PRODUCT_ID
                        LEFT JOIN PRODUCT_TEMPLATE PT ON PT.ID=PP.PRODUCT_TMPL_ID
                        LEFT JOIN IR_PROPERTY IP ON (IP.RES_ID=('product.product,' || PP.ID) AND IP.NAME='standard_price' AND IP.COMPANY_ID={company.id})
                        LEFT JOIN STOCK_LOCATION SL ON SL.ID=SML.LOCATION_DEST_ID
                        LEFT JOIN STOCK_LOCATION DL ON DL.ID=SML.LOCATION_ID
                        LEFT JOIN UOM_UOM PRODUCT_UOM ON PRODUCT_UOM.ID=PT.UOM_ID
                        LEFT JOIN UOM_UOM LINE_UOM ON LINE_UOM.ID=SML.PRODUCT_UOM_ID
            WHERE       SML.DATE <= '{end_time}' AND DL.USAGE='internal' AND SM.COMPANY_ID={company.id} 
            GROUP BY    SML.ID, SML.PRODUCT_ID, PT.DEFAULT_CODE, SML.LOCATION_DEST_ID, PT.UOM_ID, SL.USAGE, LINE_UOM.FACTOR, PRODUCT_UOM.FACTOR, IP.VALUE_FLOAT
            ) AS CLOSING  
            GROUP BY    PRODUCT_ID, LOCATION_ID
        ) CL ON (CL.PRODUCT_ID=TR.PRODUCT_ID AND CL.LOCATION_ID=TR.LOCATION_ID)
        
        GROUP BY CODE, PRODUCT, TR.PRODUCT_ID, TR.LOCATION_ID, OP.QTY, OP.VALUE, CL.QTY, CL.VALUE
        
        ORDER BY TR.LOCATION_ID, PRODUCT
        """
        _logger.info(f'\n\n\nExecuting the following query.\n\n\n{query}\n\n\n')
        if not team_ids:
            return {
                'options': options,
                'records': [],
            }
        self.env.cr.execute(query)
        records = self.env.cr.dictfetchall()

        return {
            'teams': [{
                'id': team.id,
                'name': team.name,
                'location': team.van_location_id.complete_name,
                'location_id': team.van_location_id.id,
            } for team in teams],
            'options': options,
            'transactions': records,
        }

    @api.model
    def download_report(self, report_type, data):

        if report_type == 'xlsx':
            xml_id = 'fs_inventory_report.fs_inventory_xlsx_report'
        else:
            records = []
            check_options = data.get('options')

            check_options.update({
                'report_of': 'product'
            })
            data.update({
                'options': check_options
            })
            team_ids = data.get('teams')
            for team in team_ids:
                location_id = team.get('location_id')
                line = []
                rec = data.get('transactions').get(str(location_id))
                if rec:
                    lines = rec.get('lines')
                    length = len(lines)

                    if length >= 1:
                        for line_data in lines:
                            no = 1
                            line.append({
                                "no": no,
                                'code': line_data.get('code') or '',
                                'product': line_data.get('product') or '',
                                'closing_qty': line_data.get('closing_qty') or 0.0,
                                'closing_value': line_data.get('closing_value') or 0.0
                            })
                            no += 1

                records.append({
                    'location_id': team.get('location_id'),
                    'team_name': team.get('name'),
                    'name': team.get('name') + '-' + team.get('location'),
                    'location_name': team.get('location'),
                    'lines': line
                })
            data.update({
                'records': records
            })
            xml_id = 'fs_inventory_report.fs_inventory_pdf_report'





        return self.env.ref(xml_id).report_action([1], data=data)

    # @api.model
    # def download_report(self, report_type, data):
    #     import pdb
    #     pdb.set_trace()
    #     return self.env.ref(f'fs_inventory_report.fs_inventory_{report_type}_report').report_action(docids=[], data=data)
