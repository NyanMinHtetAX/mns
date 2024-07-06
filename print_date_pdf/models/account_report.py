from odoo import models, fields
import io
from odoo.tools.misc import xlsxwriter
from datetime import datetime
from dateutil.relativedelta import relativedelta


class AccountReport(models.AbstractModel):
    _inherit = 'account.report'

    def get_xlsx(self, options, response=None):
        ####################################################
        # Overwrite this method cuz i want to add          #
        # extra formatStyle, and add default header rows   #
        # when xlsx file is generating                     #
        ####################################################
        self = self.with_context(self._set_context(options))
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {
            'in_memory': True,
            'strings_to_formulas': False,
        })
        sheet = workbook.add_worksheet(self._get_report_name()[:31])
        date_default_col1_style = workbook.add_format(
            {'font_name': 'Arial', 'font_size': 12, 'font_color': '#666666', 'indent': 2, 'num_format': 'yyyy-mm-dd'})
        date_default_style = workbook.add_format(
            {'font_name': 'Arial', 'font_size': 12, 'font_color': '#666666', 'num_format': 'yyyy-mm-dd'})
        default_col1_style = workbook.add_format(
            {'font_name': 'Arial', 'font_size': 12, 'font_color': '#666666', 'indent': 2})
        default_style = workbook.add_format({'font_name': 'Arial', 'font_size': 12, 'font_color': '#666666'})
        title_style = workbook.add_format({'font_name': 'Arial', 'bold': True, 'bottom': 2})
        level_0_style = workbook.add_format(
            {'font_name': 'Arial', 'bold': True, 'font_size': 13, 'bottom': 6, 'font_color': '#666666'})
        level_1_style = workbook.add_format(
            {'font_name': 'Arial', 'bold': True, 'font_size': 13, 'bottom': 1, 'font_color': '#666666'})
        level_2_col1_style = workbook.add_format(
            {'font_name': 'Arial', 'bold': True, 'font_size': 12, 'font_color': '#666666', 'indent': 1})
        level_2_col1_total_style = workbook.add_format(
            {'font_name': 'Arial', 'bold': True, 'font_size': 12, 'font_color': '#666666'})
        level_2_style = workbook.add_format(
            {'font_name': 'Arial', 'bold': True, 'font_size': 12, 'font_color': '#666666'})
        level_3_col1_style = workbook.add_format(
            {'font_name': 'Arial', 'font_size': 12, 'font_color': '#666666', 'indent': 2})
        level_3_col1_total_style = workbook.add_format(
            {'font_name': 'Arial', 'bold': True, 'font_size': 12, 'font_color': '#666666', 'indent': 1})
        level_3_style = workbook.add_format({'font_name': 'Arial', 'font_size': 12, 'font_color': '#666666'})

        # Set the first column width to 50
        sheet.set_column(0, 0, 50)

        y_offset = 0
        headers, lines = self.with_context(no_format=True, print_mode=True, prefetch_fields=False)._get_table(options)

        # Generate newly empty header for these reports
        if self._get_report_name() in ['Balance Sheet', 'Profit and Loss', 'Depreciation Schedule']:
            headers = [
                [{'name': '', 'class': 'number', 'colspan': 1}, {'name': '', 'class': 'number', 'colspan': 1}]]
        sheet.set_row(0, 30)
        ###################
        #  Extra formats
        title_left_style = workbook.add_format(
            {'font_name': 'Arial', 'bold': True, 'font_size': 14, 'valign': 'vcenter', 'align': 'left',
             'indent': 1})
        title_left_style_small = workbook.add_format(
            {'font_name': 'Arial', 'bold': True, 'font_size': 11, 'valign': 'vcenter', 'align': 'left',
             'indent': 1})

        ###############################
        # Add Extra Default Headers
        print_date = (datetime.now() + relativedelta(hours=6, minutes=30)).strftime('%Y-%m-%d - %H:%M:%S')
        date_filter = options.get('date', {})
        accounts = options.get('account_type', False)
        try:
            col_sizes = len(headers[0])
        except:
            col_sizes = len(headers)

        if self._get_report_name() == 'Trial Balance': col_sizes = (col_sizes * 2) - 1

        third_row_title = [
            {'name': 'Print Date', 'class': 'text', 'colspan': 1, 'format': title_left_style},
        ]

        third_row_title.append(
            {'name': print_date, 'class': 'text', 'colspan': (col_sizes - 1), 'format': title_left_style_small})

        fourth_row_title = [
            {'name': ' ', 'class': 'text', 'colspan': 1, 'format': title_left_style},
            {'name': f'{date_filter.get("string", " ")}', 'class': 'text', 'colspan': (col_sizes - 1),
             'format': title_left_style_small}
        ]

        headers.insert(0, [])  # Add empty row for line spacing
        headers.insert(0, fourth_row_title)
        headers.insert(0, third_row_title)

        # Add headers.
        for header in headers:
            x_offset = 0
            for column in header:
                column_name_formated = column.get('name', '').replace('<br/>', ' ').replace('&nbsp;', ' ')
                colspan = column.get('colspan', 1)

                #############################################
                # Get specific format defined in columns
                col_format = column.get('format', title_style)
                if colspan == 1:
                    sheet.write(y_offset, x_offset, column_name_formated, col_format)
                else:
                    sheet.merge_range(y_offset, x_offset, y_offset, x_offset + colspan - 1, column_name_formated,
                                      col_format)
                x_offset += colspan
            y_offset += 1

        if options.get('hierarchy'):
            lines = self.with_context(no_format=True)._create_hierarchy(lines, options)
        if options.get('selected_column'):
            lines = self._sort_lines(lines, options)

        # Add lines.
        for y in range(0, len(lines)):
            level = lines[y].get('level')
            if lines[y].get('caret_options'):
                style = level_3_style
                col1_style = level_3_col1_style
            elif level == 0:
                y_offset += 1
                style = level_0_style
                col1_style = style
            elif level == 1:
                style = level_1_style
                col1_style = style
            elif level == 2:
                style = level_2_style
                col1_style = 'total' in lines[y].get('class', '').split(
                    ' ') and level_2_col1_total_style or level_2_col1_style
            elif level == 3:
                style = level_3_style
                col1_style = 'total' in lines[y].get('class', '').split(
                    ' ') and level_3_col1_total_style or level_3_col1_style
            else:
                style = default_style
                col1_style = default_col1_style

            # write the first column, with a specific style to manage the indentation
            cell_type, cell_value = self._get_cell_type_value(lines[y])
            if cell_type == 'date':
                sheet.write_datetime(y + y_offset, 0, cell_value, date_default_col1_style)
            else:
                sheet.write(y + y_offset, 0, cell_value, col1_style)

            # write all the remaining cells
            for x in range(1, len(lines[y]['columns']) + 1):
                cell_type, cell_value = self._get_cell_type_value(lines[y]['columns'][x - 1])
                if cell_type == 'date':
                    sheet.write_datetime(y + y_offset, x + lines[y].get('colspan', 1) - 1, cell_value,
                                         date_default_style)
                else:
                    sheet.write(y + y_offset, x + lines[y].get('colspan', 1) - 1, cell_value, style)

        workbook.close()
        output.seek(0)
        generated_file = output.read()
        output.close()

        return generated_file
