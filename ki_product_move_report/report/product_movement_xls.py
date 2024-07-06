# -*- coding: utf-8 -*-
import pytz

from datetime import datetime
from dateutil.relativedelta import relativedelta
from odoo import models,_, api, fields


class ProductMovementReportXls(models.AbstractModel):
    _name = 'report.ki_product_move_report.product_movement_report_xlsx.xlsx'
    _inherit = 'report.report_xlsx.abstract'
    _description = 'Product Move Report'

    @api.model
    def _compute_date_range(self, data):
        date_list = []
        no_of_months = data.get('no_of_months', 1)
        current_date = fields.Date.today()
        first_date = fields.Date.to_string(current_date.replace(day=1))
        first_date = datetime.strptime(first_date, "%Y-%m-%d").date()

        for r in range(0, no_of_months):
            start_date = first_date - relativedelta(months=r)
            end_date =  start_date + relativedelta(day=31)
            date_list.append((start_date, end_date))
        date_list.reverse()
        return date_list

    @api.model
    def _get_lines(self, data):
        date_ranges=self._compute_date_range(data)

        product_data = {}

        pos_line_obj = self.env['pos.order.line'].sudo()

        if data.get('report_type', '') == 'slow_moving': 
            for date_range in date_ranges:
                domain = [
                    ('order_id.date_order', '>=', date_range[0]),
                    ('order_id.date_order', '<=', date_range[1]),
                    ('order_id.state', 'not in', ['cancel']),
                ]
                sale_lines = pos_line_obj.search(domain)
                if not data.get('group_by_category', False):
                    for line in sale_lines:
                        if line.order_id.picking_type_id.warehouse_id and line.order_id.picking_type_id.warehouse_id.id not in data['warehouse_ids']:
                            continue
                        if line.product_id not in product_data:
                            product_data.update({
                                line.product_id : {
                                    date_range[0]: 0.0
                                }
                            })
                        
                        if date_range[0] not in product_data[line.product_id]:
                            product_data[line.product_id].update({
                                date_range[0]: 0.0
                            })
                        product_data[line.product_id][date_range[0]] += line.qty
                else:
                    for line in sale_lines:
                        if line.order_id.picking_type_id.warehouse_id and line.order_id.picking_type_id.warehouse_id.id not in data['warehouse_ids']:
                            continue
    
                        if line.product_id.categ_id not in product_data:
                            product_data.update({line.product_id.categ_id: {}})
    
                        if line.product_id not in product_data[line.product_id.categ_id]:
                            product_data[line.product_id.categ_id].update({
                                line.product_id : {
                                    date_range[0]: 0.0
                                }
                            })
                        
                        if date_range[0] not in product_data[line.product_id.categ_id][line.product_id]:
                            product_data[line.product_id.categ_id][line.product_id].update({
                                date_range[0]: 0.0
                            })
                        product_data[line.product_id.categ_id][line.product_id][date_range[0]] += line.qty
        else:
            first_date = date_ranges[0][0]
            last_date = date_ranges[-1:][0][1]
            self._cr.execute("""
            SELECT
                p.id
            from
                product_product p
                left join pos_order_line pol on (pol.product_id=p.id)
                left join pos_order po on (pol.order_id=po.id)
            where
                pol.id is not null and
                po.date_order >= '%s' and
                po.date_order <= '%s';
            """ %(first_date.strftime("%Y-%m-%d"),
                  last_date.strftime("%Y-%m-%d")))
            
            product_res = self._cr.dictfetchall()
            product_ids = [p['id'] for p in product_res]
            
            # self._cr.execute("""SELECT p.id from product_product p where p.id not in %s"""%(tuple(product_ids),))
            self.env.cr.execute( 'SELECT P.ID FROM PRODUCT_PRODUCT P WHERE P.ID NOT IN %s', (tuple(product_ids), ))
            non_product_res = self._cr.dictfetchall()
            non_product_ids = [p['id'] for p in non_product_res]
            products = self.env['product.product'].sudo().browse(non_product_ids)
            for product in products:
                for date_range in date_ranges:
                    if not data.get('group_by_category', False):
                        if product.warehouse_id and product.warehouse_id.id not in data['warehouse_ids']:
                            continue
                        if product not in product_data:
                            product_data.update({
                                product : {
                                    date_range[0]: 0.0
                                }
                            })
                        
                        if date_range[0] not in product_data[product]:
                            product_data[product].update({
                                date_range[0]: 0.0
                            })
                        product_data[product][date_range[0]] += 0
                    else:
                        if product.warehouse_id and product.warehouse_id.id not in data['warehouse_ids']:
                            continue
    
                        if product.categ_id not in product_data:
                            product_data.update({product.categ_id: {}})
    
                        if product not in product_data[product.categ_id]:
                            product_data[product.categ_id].update({
                                product : {
                                    date_range[0]: 0.0
                                }
                            })
                        
                        if date_range[0] not in product_data[product.categ_id][product]:
                            product_data[product.categ_id][product].update({
                                date_range[0]: 0.0
                            })
        return product_data

    def generate_xlsx_report(self, workbook, data, lines):
        company = self.env.user.company_id
        
        data_form = data['form']
        company_id = data_form.get('company_id', False)
        company = self.env['res.company'].sudo().browse(company_id)

        warehouse_ids = data_form.get('warehouse_ids', [])
        warehouse_ids = self.env['stock.warehouse'].browse(warehouse_ids)

        product_obj = self.env['product.product'].sudo()

        y_offset = 0

        sheet = workbook.add_worksheet('Product Movement Report')
        format0 = workbook.add_format({
            'bold': True,'align': 'center','font_size': 14
        })
        format1 = workbook.add_format({
            'bold': True,'bg_color': '#FFFFCC','border': True,'align': 'left'
        })
        format2 = workbook.add_format({'border': True,'align': 'left',})
        format5 = workbook.add_format({'align': 'left','bold': True, 'top': True})
        format5_2 = workbook.add_format({'align': 'left','bold': True})
        format5_1 = workbook.add_format({'align': 'left',})
        format5_border_top = workbook.add_format({'align': 'left', 'top': True})
        format3 = workbook.add_format({
            'align': 'center','bold': True,'border': True
        })
        format4 = workbook.add_format({'border': True,'align': 'left'})
        font_size_8 = workbook.add_format({'border': True,'align': 'center'})
        red_mark = workbook.add_format({'font_size': 8, 'bg_color': 'red'})
        justify = workbook.add_format({'font_size': 12})
        sheet.set_column('A:A', 30)
        sheet.set_column('B:B', 30)
        sheet.merge_range(y_offset, 0, y_offset, 1, _('Product Movement Report'), format0)
        y_offset += 2

        company_name =  company.name
        warehouse_name = ', '.join([w.display_name for w in warehouse_ids])

        sheet.write(y_offset, 0, _('COMPANY NAME:'), format1)
        sheet.write(y_offset, 1, company_name or '', format2)
        y_offset += 1
        sheet.write(y_offset, 0, _('WAREHOUSE NAME:'), format1)
        sheet.write(y_offset, 1,warehouse_name or '', format2)
        y_offset += 3

        x_offset = 0

        sheet.write(y_offset, x_offset, _('NO'), format3)
        x_offset += 1

        sheet.write(y_offset, x_offset, _('PRODUCT REF'), format3)
        x_offset += 1

        sheet.write(y_offset, x_offset, _('BARCODE'), format3)
        x_offset += 1

        sheet.write(y_offset, x_offset, _('PRODUCT NAME'), format3)
        x_offset += 1

        sheet.write(y_offset, x_offset, _('UOM'), format3)
        x_offset += 1

        sheet.write(y_offset, x_offset, _('COST'), format3)
        x_offset += 1

        sheet.write(y_offset, x_offset, _('SALES PRICE'), format3)
        x_offset += 1

        date_list = self._compute_date_range(data_form)
        for date_l in date_list:
            sheet.write(y_offset, x_offset, date_l[0].strftime("%b").upper(), format3)
            x_offset += 1

        sheet.write(y_offset, x_offset, _('AVERAGE SALE'), format3)
        x_offset += 1

        sheet.write(y_offset, x_offset, _('MONTH TO SELL'), format3)
        x_offset += 1

        sheet.write(y_offset, x_offset, _('QUANTITY ON HAND'), format3)

        if data_form.get('report_type', '') == 'slow_moving':
            x_offset += 1
            sheet.write(y_offset, x_offset, _('SLOW MOVING %'), format3)

        lines = self._get_lines(data_form)

        if not data_form.get('group_by_category', False):
 
            i = 1
            y_offset += 1
            for product in lines:
                rx_offset = 0

                if product.qty_available <= 0.0:
                    continue

                if data_form.get('report_type', '') == 'non_moving':
                    qty = sum(lines[product][l] for l in lines[product])
                    avg_sale = qty / 4#data_form['no_of_months']
                    ratio = 0.0
                    if product.qty_available > 0.0:
#                         ratio = (avg_sale * 2.00) / product.qty_available
                        ratio = (avg_sale / (product.qty_available / 2.0)) * 100.0
                    if ratio > 0.0 or product.qty_available <= 0.0:
                        continue
                else:
                    qty = sum(lines[product][l] for l in lines[product])
                    avg_sale = qty / 4#data_form['no_of_months']
                    ratio = 0.0
                    if product.qty_available > 0.0:
#                         ratio = (avg_sale * 2.00) / product.qty_available
                        ratio = (avg_sale / (product.qty_available / 2.0)) * 100.0

                    if product.qty_available == 0.0 or ratio >= 100.0 or ratio <= 0.0:
                        continue

                sheet.write(y_offset, rx_offset, i, format5_1)
                rx_offset += 1

                prod_name = product.name_get()[0][1]

                sheet.write(y_offset, rx_offset, product.default_code or '', format5_1)
                rx_offset += 1

                sheet.write(y_offset, rx_offset, product.barcode or '', format5_1)
                rx_offset += 1

                sheet.write(y_offset, rx_offset, prod_name, format5_1)
                rx_offset += 1

                sheet.write(y_offset, rx_offset, product.uom_id.name_get()[0][1], format5_1)
                rx_offset += 1

                sheet.write(y_offset, rx_offset, product.standard_price, format5_1)
                rx_offset += 1

                sheet.write(y_offset, rx_offset, product.list_price, format5_1)
                rx_offset += 1

                qty_total = 0.0
                date_list = self._compute_date_range(data_form)
                for date_l in date_list:
                    qty = date_l[0]
                    qty_total += lines[product].get(qty, 0.0)
                    sheet.write(y_offset, rx_offset, lines[product].get(qty, 0.0), format5_1)
                    rx_offset += 1

                avg_qty = qty_total / 4#len(lines[product])
                sheet.write(y_offset, rx_offset, avg_qty, format5_1)
                rx_offset += 1

                sheet.write(y_offset, rx_offset, avg_qty and product.qty_available / avg_qty or 0.0, format5_1)
                rx_offset += 1

                sheet.write(y_offset, rx_offset, product.qty_available, format5_1)

                if data_form.get('report_type', '') == 'slow_moving':
                    rx_offset += 1
                    sheet.write(y_offset, rx_offset, (avg_qty / (product.qty_available / 2.0)) * 100.0, format5_1)

                y_offset += 1
                i += 1
        else:
            y_offset += 1
            for categ in lines:
                sheet.write(y_offset, 0, categ.display_name, format5_2)
                y_offset += 1

                i = 1
                y_offset += 1
                for product in lines[categ]:
                    rx_offset = 0

                    if product.qty_available <= 0.0:
                        continue

                    if data_form.get('report_type', '') == 'non_moving':
                        qty = sum(lines[categ][product][l] for l in lines[categ][product])
                        avg_sale = qty / data_form['no_of_months']
                        ratio = 0.0
                        if product.qty_available > 0.0:
                            ratio = (avg_sale / (product.qty_available / 2.0)) * 100.0
                        if ratio > 0.0 or product.qty_available <= 0.0:
                            continue
                    else:
                        qty = sum(lines[categ][product][l] for l in lines[categ][product])
                        avg_sale = qty / data_form['no_of_months']
                        ratio = 0.0
                        if product.qty_available > 0.0:
                            ratio = (avg_sale / (product.qty_available / 2.0)) * 100.0

                        if product.qty_available == 0.0 or ratio >= 100.0:
                            continue


                    sheet.write(y_offset, rx_offset, i, format5_1)
                    rx_offset += 1

                    prod_name = product.name_get()[0][1]

                    sheet.write(y_offset, rx_offset, product.default_code or '', format5_1)
                    rx_offset += 1

                    sheet.write(y_offset, rx_offset, product.barcode or '', format5_1)
                    rx_offset += 1

                    sheet.write(y_offset, rx_offset, prod_name, format5_1)
                    rx_offset += 1

                    sheet.write(y_offset, rx_offset, product.uom_id.name_get()[0][1], format5_1)
                    rx_offset += 1

                    sheet.write(y_offset, rx_offset, product.standard_price, format5_1)
                    rx_offset += 1

                    sheet.write(y_offset, rx_offset, product.list_price, format5_1)
                    rx_offset += 1

                    qty_total = 0.0

                    date_list = self._compute_date_range(data_form)
                    for date_l in date_list:
                        qty = date_l[0]
                        qty_total += lines[categ][product].get(qty, 0.0)
                        sheet.write(y_offset, rx_offset, lines[categ][product].get(qty, 0.0), format5_1)
                        rx_offset += 1
                    avg_qty = qty_total / 4#len(lines[categ][product])
                    sheet.write(y_offset, rx_offset, avg_qty, format5_1)
                    rx_offset += 1

                    sheet.write(y_offset, rx_offset, avg_qty and product.qty_available / avg_qty or 0.0, format5_1)
                    rx_offset += 1

                    sheet.write(y_offset, rx_offset, product.qty_available, format5_1)

                    if data_form.get('report_type', '') == 'slow_moving':
                        rx_offset += 1
                        sheet.write(y_offset, rx_offset, (avg_qty / (product.qty_available / 2.0)) * 100.0, format5_1)

                    y_offset += 1
                    i += 1
