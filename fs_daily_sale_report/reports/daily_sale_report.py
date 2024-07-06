import pytz
from datetime import datetime
from dateutil.relativedelta import relativedelta
from odoo import api, models, fields
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT, DEFAULT_SERVER_DATE_FORMAT
from odoo.exceptions import UserError
from itertools import groupby


class DailySaleReportXlsx(models.AbstractModel):

    _name = 'report.fs_daily_sale_report.daily_sale_report_xlsx'
    _inherit = 'report.report_xlsx.abstract'
    _description = 'Daily Sale Report XLSX'

    def generate_xlsx_report(self, workbook, data, docs):

        heading_style = workbook.add_format({
            'font_name': 'Arial', 'font_size': 12, 'bold': True,
            'valign': 'vcenter', 'align': 'center',
        })

        table_heading_style = workbook.add_format({
            'font_name': 'Arial', 'font_size': 11, 'bold': True,
            'valign': 'vcenter', 'align': 'left',
        })

        title_style = workbook.add_format({
            'font_name': 'Arial', 'font_size': 10, 'bold': True,
            'valign': 'vcenter', 'align': 'center',
        })

        title_left_style = workbook.add_format({
            'font_name': 'Arial', 'font_size': 10, 'bold': True,
            'valign': 'vcenter', 'align': 'left',
        })

        title_right_style = workbook.add_format({
            'font_name': 'Arial', 'font_size': 10, 'bold': True,
            'valign': 'vcenter', 'align': 'right',
        })

        header_footer_style = workbook.add_format({
            'font_name': 'Arial', 'font_size': 9, 'bold': True,
            'valign': 'vcenter', 'align': 'center', 'border': 1,
            'font_color': '#ffffff', 'bg_color': '#473e8a'
        })

        header_footer_right = workbook.add_format({
            'font_name': 'Arial', 'font_size': 9, 'bold': True,
            'valign': 'vcenter', 'align': 'right', 'border': 1,
            'font_color': '#ffffff', 'bg_color': '#473e8a'
        })

        normal_cell_style = workbook.add_format({
            'font_name': 'Arial', 'font_size': 9,
            'valign': 'vcenter', 'align': 'center', 'border': 1,
        })

        left_cell_style = workbook.add_format({
            'font_name': 'Arial', 'font_size': 9,
            'valign': 'vcenter', 'align': 'left', 'border': 1,
        })

        right_cell_style = workbook.add_format({
            'font_name': 'Arial', 'font_size': 9,
            'valign': 'vcenter', 'align': 'right', 'border': 1,
        })

        date = datetime.strptime(data['date'], DEFAULT_SERVER_DATETIME_FORMAT).strftime('%d %B, %Y')
        sheet = workbook.add_worksheet('Daily Sale Summary Report')

        # Adjust Row Height
        sheet.set_row(0, 25)
        sheet.set_row(6, 20)
        sheet.set_row(7, 20)

        # Adjust Column Width
        sheet.set_column('A:A', 5)
        sheet.set_column('B:B', 15)
        sheet.set_column('C:C', 15)
        sheet.set_column('D:G', 20)

        # Report Title
        sheet.merge_range('A1:G1', 'Daily Sale Summary Report', heading_style)

        sheet.merge_range('A2:B2', 'Date', title_left_style)
        sheet.merge_range('A3:B3', 'Sales Team', title_left_style)
        sheet.merge_range('A4:B4', 'Route Plan', title_left_style)
        sheet.merge_range('A5:B5', 'Salesman', title_left_style)
        sheet.write('C2', date, title_right_style)
        sheet.write('C3', data['sale_team']['name'], title_right_style)
        sheet.write('C4', data['route_plan']['name'], title_right_style)
        sheet.write('C5', data['sale_person']['name'], title_right_style)

        sheet.write('F2', 'Total Customers', title_left_style)
        sheet.write('F3', 'Sale Orders', title_left_style)
        sheet.write('F4', 'Zero Sale Visit', title_left_style)
        sheet.write('F5', 'New Customers', title_left_style)
        sheet.write('G2', data['partner_count'], title_style)
        sheet.write('G3', data['order_count'], title_style)
        sheet.write('G4', data['zero_sale_visit_count'], title_style)
        sheet.write('G5', data['new_partner_count'], title_style)

        sheet.merge_range(f'A7:C7', 'Item Summary', table_heading_style)
        # Item Summary Table Column Headers
        sheet.write('A8', 'No.', header_footer_style)
        sheet.merge_range('B8:C8', 'Item', header_footer_style)
        sheet.write('D8', 'Qty', header_footer_style)
        sheet.write('E8', 'UoM', header_footer_style)
        sheet.write('F8', 'Unit Price', header_footer_style)
        sheet.write('G8', 'Total', header_footer_style)

        no = 1
        row_index = 9
        total_qty = total_amt = 0
        for record in data['sale_items']:
            sheet.write(f'A{row_index}', no, normal_cell_style)
            sheet.merge_range(f'B{row_index}:C{row_index}', record['item_name'], left_cell_style)
            sheet.write(f'D{row_index}', record['qty'], normal_cell_style)
            sheet.write(f'E{row_index}', record['uom'], normal_cell_style)
            sheet.write(f'F{row_index}', record['price_unit'], normal_cell_style)
            sheet.write(f'G{row_index}', record['total'], right_cell_style)
            total_qty += record['qty']
            total_amt += record['total']
            no += 1
            row_index += 1
        sheet.set_row(row_index - 1, 20)
        sheet.merge_range(f'A{row_index}:C{row_index}', 'Total Qty', header_footer_style)
        sheet.write(f'D{row_index}', total_qty, header_footer_style)
        sheet.merge_range(f'E{row_index}:F{row_index}', 'Total Amount', header_footer_style)
        sheet.write(f'G{row_index}', total_amt, header_footer_right)
        row_index += 2

        sheet.set_row(row_index - 1, 20)
        sheet.merge_range(f'A{row_index}:C{row_index}', 'Payment Summary', table_heading_style)
        row_index += 1

        # Payment Summary Table Column Headers
        sheet.set_row(row_index - 1, 20)
        sheet.write(f'A{row_index}', 'No.', header_footer_style)
        sheet.merge_range(f'B{row_index}:D{row_index}', 'Payment Method', header_footer_style)
        sheet.write(f'E{row_index}', 'Amount', header_footer_style)
        sheet.merge_range(f'F{row_index}:G{row_index}', 'Currency', header_footer_style)
        row_index += 1
        no = 1
        for record in data['payments']:
            if record['currency_position'] == 'before':
                num_format = f'{record["currency_symbol"]}#,##0.00'
            else:
                num_format = f'#,##0.00{record["currency_symbol"]}'
            currency_format = workbook.add_format({
                'font_name': 'Arial', 'font_size': 9, 'num_format': num_format,
                'valign': 'vcenter', 'align': 'right', 'border': 1,
            })
            sheet.write(f'A{row_index}', no, normal_cell_style)
            sheet.merge_range(f'B{row_index}:D{row_index}', record['payment_method'], normal_cell_style)
            sheet.write(f'E{row_index}', record['amount'], currency_format)
            sheet.merge_range(f'F{row_index}:G{row_index}', record['currency'], normal_cell_style)
            no += 1
            row_index += 1

        row_index += 1
        sheet.set_row(row_index - 1, 20)
        sheet.merge_range(f'A{row_index}:C{row_index}', 'Inventory On Hand', table_heading_style)
        row_index += 1

        # Inventory On Hand Table Column Headers
        sheet.set_row(row_index - 1, 20)
        sheet.write(f'A{row_index}', 'No.', header_footer_style)
        sheet.merge_range(f'B{row_index}:D{row_index}', 'Item', header_footer_style)
        sheet.write(f'E{row_index}', 'Qty', header_footer_style)
        sheet.merge_range(f'F{row_index}:G{row_index}', 'UOM', header_footer_style)

        no = 1
        row_index += 1
        for record in data['products_on_hand']:
            sheet.write(f'A{row_index}', no, normal_cell_style)
            sheet.merge_range(f'B{row_index}:D{row_index}', record['product'], left_cell_style)
            sheet.write(f'E{row_index}', record['qty'], normal_cell_style)
            sheet.merge_range(f'F{row_index}:G{row_index}', record['uom'], normal_cell_style)
            no += 1
            row_index += 1


class DailySaleReport(models.AbstractModel):

    _name = 'daily.sale.summary.report'
    _description = 'Daily Sale Summary Report'

    id = fields.Integer('ID')

    @api.model
    def get_data(self, date=False, team_id=False, user_id=False, route_plan_id=False):
        if not date:
            date = datetime.now().strftime(DEFAULT_SERVER_DATETIME_FORMAT)
        sale_teams = self.env['crm.team'].search([('is_van_team', '=', True),
                                                  ('company_id', '=', self.env.company.id)])
        sale_teams = [{'id': team.id, 'name': team.name} for team in sale_teams]
        if not sale_teams:
            raise UserError('Sale team is not yet create. Please create at least one sale team')
        delta = relativedelta(hours=6, minutes=30)
        date = datetime.strptime(date, DEFAULT_SERVER_DATETIME_FORMAT)
        start_time = (datetime.combine(date.date(), datetime.min.time()) - delta).strftime('%Y-%m-%d %H:%M:%S')
        end_time = (datetime.combine(date.date(), datetime.max.time()) - delta).strftime('%Y-%m-%d %H:%M:%S')
        # Options
        if not team_id:
            team_id = team_id if team_id else sale_teams[0]['id']
        team = self.env['crm.team'].browse(team_id)
        if not user_id:
            sale_persons = team.member_ids.filtered_domain([('company_id', '=', self.env.company.id)])
            user_id = sale_persons[0].id if sale_persons else False
        if not route_plan_id:
            route_plan_ids = team.route_plan_ids
            route_plan_id = route_plan_ids[0].id if route_plan_ids else False

        route_plans = self.env['route.plan'].search([('company_id', '=', self.env.company.id)])
        route_plans = [{'id': route_plan.id, 'name': route_plan.name} for route_plan in route_plans]

        sale_persons = self.env['crm.team'].search([('is_van_team', '=', True)]).member_ids.filtered(lambda sp: sp.company_id == self.env.company)
        sale_persons = [{'id': sale_person.id, 'name': sale_person.name} for sale_person in sale_persons]

        company = self.env.company
        company_currency = company.currency_id

        if team_id and user_id and route_plan_id:
            self.env.cr.execute(f"""
            SELECT      VOL.PRODUCT_ID,
                        PT.NAME AS ITEM_NAME,
                        SUM(VOL.QTY) AS QTY,
                        UOM.NAME AS UOM,
                        VOL.PRICE_UNIT AS PRICE_UNIT,
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
                        LEFT JOIN DAILY_SALE_SUMMARY DSS ON DSS.ID=VO.DAILY_SALE_SUMMARY_ID
                        LEFT JOIN MULTI_UOM_LINE MUL ON MUL.ID=VOL.MULTI_UOM_LINE_ID
                        LEFT JOIN UOM_UOM UOM ON UOM.ID=MUL.UOM_ID
                        LEFT JOIN PRODUCT_PRODUCT PP ON PP.ID=VOL.PRODUCT_ID
                        LEFT JOIN PRODUCT_TEMPLATE PT ON PT.ID=PP.PRODUCT_TMPL_ID

            WHERE       VO.DATE BETWEEN %s AND %s AND 
                        VO.STATE != 'cancel' AND
                        VO.TEAM_ID = %s AND
                        DSS.ROUTE_PLAN_ID = %s AND
                        VO.USER_ID = %s AND
                        VO.COMPANY_ID = %s

            GROUP BY    VOL.PRODUCT_ID,
                        VOL.MULTI_UOM_LINE_ID,
                        VOL.PRICE_UNIT,
                        PT.NAME,
                        UOM.NAME

            ORDER BY    VOL.PRODUCT_ID,
                        VOL.MULTI_UOM_LINE_ID,
                        VOL.PRICE_UNIT
                    """, (start_time, end_time, team_id, route_plan_id, user_id, self.env.company.id))
            sale_items = self.env.cr.dictfetchall()
            query = """
            SELECT      VOL.PRODUCT_ID,
                        PT.NAME AS ITEM_NAME,
                        SUM(VOL.QTY) AS QTY,
                        UOM.NAME AS UOM,
                        VOL.PRICE_UNIT AS PRICE_UNIT,
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
                        LEFT JOIN DAILY_SALE_SUMMARY DSS ON DSS.ID=VO.DAILY_SALE_SUMMARY_ID
                        LEFT JOIN MULTI_UOM_LINE MUL ON MUL.ID=VOL.MULTI_UOM_LINE_ID
                        LEFT JOIN UOM_UOM UOM ON UOM.ID=MUL.UOM_ID
                        LEFT JOIN PRODUCT_PRODUCT PP ON PP.ID=VOL.PRODUCT_ID
                        LEFT JOIN PRODUCT_TEMPLATE PT ON PT.ID=PP.PRODUCT_TMPL_ID

            WHERE       VO.DATE BETWEEN %s AND %s AND 
                        VO.STATE != 'cancel' AND
                        VO.TEAM_ID = %s AND
                        DSS.ROUTE_PLAN_ID = %s AND
                        VO.USER_ID = %s AND
                        VO.COMPANY_ID = %s

            GROUP BY    VOL.PRODUCT_ID,
                        VOL.MULTI_UOM_LINE_ID,
                        VOL.PRICE_UNIT,
                        PT.NAME,
                        UOM.NAME

            ORDER BY    VOL.PRODUCT_ID,
                        VOL.MULTI_UOM_LINE_ID,
                        VOL.PRICE_UNIT 
            """
            self.env.cr.execute("""
            SELECT      FPM.NAME AS PAYMENT_METHOD,
                        CUR.NAME AS CURRENCY,
                        CUR.SYMBOL AS CURRENCY_SYMBOL,
                        CUR.POSITION AS CURRENCY_POSITION,
                        SUM(VOP.AMOUNT) AS AMOUNT
            
            FROM        VAN_ORDER_PAYMENT VOP
                        LEFT JOIN FIELDSALE_PAYMENT_METHOD FPM ON FPM.ID=VOP.PAYMENT_METHOD_ID
                        LEFT JOIN RES_CURRENCY CUR ON CUR.ID=VOP.CURRENCY_ID
                        LEFT JOIN VAN_ORDER VO ON VO.ID=VOP.ORDER_ID
                        LEFT JOIN DAILY_SALE_SUMMARY DSS ON DSS.ID=VO.DAILY_SALE_SUMMARY_ID
                        
            WHERE       VO.DATE BETWEEN %s AND %s AND 
                        VO.STATE != 'cancel' AND
                        VO.TEAM_ID = %s AND
                        DSS.ROUTE_PLAN_ID = %s AND
                        VO.USER_ID = %s AND
                        VO.COMPANY_ID = %s
            
            GROUP BY    FPM.NAME,
                        CUR.NAME,
                        CUR.SYMBOL,
                        CUR.POSITION
            
            ORDER BY    FPM.NAME,
                        CUR.NAME
            """, (start_time, end_time, team_id, route_plan_id, user_id, self.env.company.id))
            payments = self.env.cr.dictfetchall()

            user_tz = pytz.timezone(self.env.context.get('tz') or 'utc')
            inventory_date = datetime.strptime(start_time, '%Y-%m-%d %H:%M:%S')
            inventory_date = pytz.utc.localize(inventory_date, is_dst=None).astimezone(user_tz)
            
            products_on_hand = self.env['stock.quant'].with_context(inventory_date=inventory_date).search([
                ('location_id', '=', team.van_location_id.id),
                ('quantity', '>', 0),
            ])
            products_on_hand = [{
                'product': product.product_id.name,
                'qty': product.quantity,
                'uom': product.product_uom_id.name,
            } for product in products_on_hand]
            orders = self.env['van.order'].search([('date', '>=', start_time),
                                                   ('date', '<=', end_time),
                                                   ('team_id', '=', team_id),
                                                   ('user_id', '=', user_id),
                                                   ('daily_sale_summary_id.route_plan_id', '=', route_plan_id),
                                                   ('state', '!=', 'cancel')])
            
            new_partners = self.env['res.partner'].search([('is_mobile_customer', '=', True),('company_id','=',self.env.company.id),
                                                           ('create_date', '>=', start_time)])
            visit_reports = self.env['visit.report'].search([('date', '=', date.date()),
                                                             ('sale_team', '=', team_id),
                                                             ('sale_man', '=', user_id)])
            partner_count = len(orders.partner_id)
            order_count = len(orders)
            new_partner_count = len(new_partners)
            zero_sale_visit_count = len(visit_reports)
        else:
            sale_items = payments = products_on_hand = []
            partner_count = order_count = new_partner_count = zero_sale_visit_count = 0
        no_data = {'id': False, 'name': '-'}
        if not sale_items and not payments and not products_on_hand:
            data_available = False
        else:
            data_available = True
        return {
            'date': date,
            'sale_person': [sp for sp in sale_persons if sp['id'] == user_id][0] if user_id is not False else no_data,
            'sale_persons': sale_persons,
            'route_plan': [rp for rp in route_plans if rp['id'] == route_plan_id][0] if route_plan_id is not False else no_data,
            'route_plans': route_plans,
            'sale_team': [st for st in sale_teams if st['id'] == team_id][0] if team_id is not False else no_data,
            'sale_teams': sale_teams,
            'sale_items': sale_items,
            'payments': payments,
            'products_on_hand': products_on_hand,
            'partner_count': partner_count,
            'order_count': order_count,
            'new_partner_count': new_partner_count,
            'zero_sale_visit_count': zero_sale_visit_count,
            'data_available': data_available,
        }

    @api.model
    def download_report(self, report_type, data):
        data['total_qty'] = sum([rec['qty'] for rec in data['sale_items']])
        data['total_amt'] = sum([rec['total'] for rec in data['sale_items']])
        if report_type == 'xlsx':
            xml_id = 'fs_daily_sale_report.daily_sale_summary_xlsx_report'
        else:
            xml_id = 'fs_daily_sale_report.daily_sale_summary_pdf_report'
        return self.env.ref(xml_id).report_action(docids=[], data=data)
