from dateutil.relativedelta import relativedelta

from odoo import api, models, fields, _
import datetime

from odoo.exceptions import UserError


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    sale_person_id = fields.Many2one('res.users', 'Sale Person')
    helper_id = fields.Many2one('hr.employee', 'Helper Name')
    purchaser_id = fields.Many2one('res.users', 'Purchaser')

    def get_delivery_order_b5_pdf_report(self):
        records = []
        no = 1
        print_date = datetime.datetime.now() + relativedelta(hours=6, minutes=30)
        for order in self:
            total_qty_done = 0
            move_ids = order.move_ids_without_package
            report_template_id = []
            if order.report_template_id:
                for temp in order.report_template_id:
                    report_template_id.append({
                        'title_img': temp.image_1920 or False,
                        'title1': temp.title1 or '',
                        'title2': temp.title2 or '',
                        'address': temp.address or '',
                        'company_phone': temp.company_phone or '',
                        'social_viber': temp.social_viber or '',
                        'social_mail': temp.social_mail or '',
                        'thank': temp.thank or '',
                        'complain': temp.complain or '',
                    })
            else:
                raise UserError(_('Please Insert Report Template '))
            if move_ids:
                for move_id in move_ids:
                    total_qty_done += move_id.multi_quantity_done
            move_ids_without_package = []
            for move in order.move_ids_without_package:
                move_ids_without_package.append({
                    'sr': no,
                    'pcode': move.product_id.default_code or '',
                    'product': move.product_id.name or '',
                    'uom': move.multi_uom_line_id.uom_id.name or '',
                    'qty': move.multi_quantity_done or '0',
                })
                no += 1

            records.append({
                'printed_date': print_date.strftime('%d-%m-%Y %I:%M:%S %p'),
                'vehicle_no': order.license_plate or '',
                'driver': order.driver_id.name or '',
                'car_gate': order.partner_id.name or '',
                'effective_date': order.scheduled_date.strftime('%d-%m-%Y') or '',
                'sale_person': order.sale_person_id.name or '',
                'total_qty_done': total_qty_done or '0',
                'remark': order.remark or '',
                'helper': order.helper_id.name or '',
                'move_ids_without_package': move_ids_without_package,
                'report_template_id': report_template_id,
            })
        return self.env.ref('report_form.action_delivery_order_b5_pdf_report').report_action(self, data={
            'records': records,
        })

    def get_delivery_order_cargate_b5_pdf_report(self):
        records = []
        no = 1
        print_date = datetime.datetime.now() + relativedelta(hours=6, minutes=30)
        for order in self:
            total_qty_done = 0
            move_ids = order.move_ids_without_package
            report_template_id = []
            if order.report_template_id:
                for temp in order.report_template_id:
                    report_template_id.append({
                        'title_img': temp.image_1920 or False,
                        'title1': temp.title1 or '',
                        'title2': temp.title2 or '',
                        'address': temp.address or '',
                        'company_phone': temp.company_phone or '',
                        'social_viber': temp.social_viber or '',
                        'social_mail': temp.social_mail or '',
                        'thank': temp.thank or '',
                        'complain': temp.complain or '',
                    })
            else:
                raise UserError(_('Please Insert Report Template '))
            if move_ids:
                for move_id in move_ids:
                    total_qty_done += move_id.multi_quantity_done
            move_ids_without_package = []
            for move in order.move_ids_without_package:
                move_ids_without_package.append({
                    'sr': no,
                    'pcode': move.product_id.default_code or '',
                    'product': move.product_id.name or '',
                    'uom': move.multi_uom_line_id.uom_id.name or '',
                    'qty': move.multi_quantity_done or '0',
                })
                no += 1

            records.append({
                'printed_date': print_date.strftime('%d-%m-%Y %I:%M:%S %p'),
                'vehicle_no': order.license_plate or '',
                'driver': order.driver_id.name or '',
                'car_gate': order.partner_id.name or '',
                'effective_date': order.scheduled_date.strftime('%d-%m-%Y') or '',
                'sale_person': order.sale_person_id.name or '',
                'remark': order.remark or '',
                'helper': order.helper_id.name or '',
                'total_qty_done': total_qty_done or '0',
                'move_ids_without_package': move_ids_without_package,
                'report_template_id': report_template_id,
            })
        return self.env.ref('report_form.action_delivery_order_cargate_b5_pdf_report').report_action(self, data={
            'records': records,
        })

    def get_return_in_pdf_report(self):
        records = []
        company = []
        print_date = datetime.datetime.now() + relativedelta(hours=6, minutes=30)
        no = 1
        for order in self:
            total_qty_done = 0
            move_ids = order.move_ids_without_package
            report_template_id = []
            if order.report_template_id:
                for temp in order.report_template_id:
                    report_template_id.append({
                        'title_img': temp.image_1920 or False,
                        'title1': temp.title1 or '',
                        'title2': temp.title2 or '',
                        'address': temp.address or '',
                        'company_phone': temp.company_phone or '',
                        'social_viber': temp.social_viber or '',
                        'social_mail': temp.social_mail or '',
                        'thank': temp.thank or '',
                        'complain': temp.complain or '',
                    })
            else:
                raise UserError(_('Please Insert Report Template '))
            if move_ids:
                for move_id in move_ids:
                    total_qty_done += move_id.multi_quantity_done
            move_ids_without_package = []
            for move in order.move_ids_without_package:
                move_ids_without_package.append({
                    'no': no,
                    'pcode': move.product_id.default_code or '',
                    'product': move.product_id.name or '',
                    'uom': move.multi_uom_line_id.uom_id.name or '',
                    'qty': move.multi_quantity_done or '0',
                })
                no += 1

            records.append({
                'printed_date': print_date.strftime('%d-%m-%Y %I:%M:%S %p'),
                'name': order.name or '',
                'vol_no': order.origin or '',
                'customer_id': order.partner_id.name or '',
                'sale_person': order.sale_person_id.name or '',
                'received_date': order.scheduled_date.strftime('%d-%m-%Y') or '',
                'remark': order.remark or '',
                'warehouse_location': order.location_dest_id.location_id.name or '',
                'warehouse_dest': order.location_dest_id.name or '',
                'qty_total': total_qty_done or '0',
                'moves': move_ids_without_package,
                'report_template_id': report_template_id,
            })
            company.append({

                'company_name': self.company_id.name,
                'image': self.company_id.logo,
                'phone': self.company_id.phone or '',
                'street1': self.company_id.street or '',
                'street2': self.company_id.street2 or '',
                'township': self.company_id.township_id.name or '',
                'city': self.company_id.city or '',
                'gmail': self.company_id.email or '',
                'website': self.company_id.website or '',
                'facebook_link': self.company_id.partner_id.facebook_link or '',
                'viber_no': self.company_id.partner_id.viber_no or '',
                'we_chat': self.company_id.partner_id.we_chat or '',
            })
        return self.env.ref('report_form.action_return_in_b5_pdf_report').report_action(self, data={
            'records': records,
            'company': company,
        })

    def get_return_out_pdf_report(self):
        records = []
        company = []
        no = 1
        print_date = datetime.datetime.now() + relativedelta(hours=6, minutes=30)
        for order in self:
            total_qty_done = 0
            move_ids = order.move_ids_without_package
            report_template_id = []
            if order.report_template_id:
                for temp in order.report_template_id:
                    report_template_id.append({
                        'title_img': temp.image_1920 or False,
                        'title1':temp.title1 or '',
                        'title2':  temp.title2 or '',
                        'address': temp.address or '',
                        'company_phone': temp.company_phone or '',
                        'social_viber': temp.social_viber or '',
                        'social_mail': temp.social_mail or '',
                        'thank': temp.thank or '',
                        'complain': temp.complain or '',
                    })
            else:
                raise UserError(_('Please Insert Report Template '))
            if move_ids:
                for move_id in move_ids:
                    total_qty_done += move_id.multi_quantity_done
            move_ids_without_package = []
            for move in order.move_ids_without_package:
                move_ids_without_package.append({
                    'no': no,
                    'pcode': move.product_id.default_code or '',
                    'product': move.product_id.name or '',
                    'uom': move.multi_uom_line_id.uom_id.name or '',
                    'qty': move.multi_quantity_done or '0',
                })
                no += 1

            records.append({
                'printed_date': print_date.strftime('%d-%m-%Y %I:%M:%S %p'),
                'name': order.name or '',
                'vol_no': order.origin or '',
                'customer_id': order.partner_id.name or '',
                'sale_person': order.sale_person_id.name or '',
                'received_date': order.scheduled_date.strftime('%d-%m-%Y') or '',
                'remark': order.remark or '',
                'warehouse_location': order.location_dest_id.location_id.name or '',
                'warehouse_dest': order.location_dest_id.name or '',
                'qty_total': total_qty_done or '0',
                'moves': move_ids_without_package,
                'report_template_id': report_template_id,
            })
            company.append({

                'company_name': self.company_id.name,
                'image': self.company_id.logo,
                'phone': self.company_id.phone or '',
                'street1': self.company_id.street or '',
                'street2': self.company_id.street2 or '',
                'township': self.company_id.township_id.name or '',
                'city': self.company_id.city or '',
                'gmail': self.company_id.email or '',
                'website': self.company_id.website or '',
                'facebook_link': self.company_id.partner_id.facebook_link or '',
                'viber_no': self.company_id.partner_id.viber_no or '',
                'we_chat': self.company_id.partner_id.we_chat or '',
            })
        return self.env.ref('report_form.action_return_out_b5_pdf_report').report_action(self, data={
            'records': records,
            'company': company,
        })

    def get_grn_b5_pdf_report(self):
        records = []
        no = 1
        print_date = datetime.datetime.now() + relativedelta(hours=6, minutes=30)
        for order in self:
            total_qty_done = 0
            move_ids = order.move_ids_without_package
            report_template_id = []
            if order.report_template_id:
                for temp in order.report_template_id:
                    report_template_id.append({
                        'title_img': temp.image_1920 or False,
                        'title1': temp.title1 or '',
                        'title2': temp.title2 or '',
                        'address': temp.address or '',
                        'company_phone': temp.company_phone or '',
                        'social_viber': temp.social_viber or '',
                        'social_mail': temp.social_mail or '',
                        'thank': temp.thank or '',
                        'complain': temp.complain or '',
                    })
            else:
                raise UserError(_('Please Insert Report Template '))

            if move_ids:
                for move_id in move_ids:
                    total_qty_done += move_id.multi_quantity_done
            move_ids_without_package = []
            balance_qty = 0

            for move in order.move_ids_without_package:
                balance_qty = move.multi_uom_qty - move.multi_quantity_done
                move_ids_without_package.append({
                    'sr': no,
                    'pcode': move.product_id.default_code or '',
                    'product': move.product_id.name or '',
                    'uom': move.multi_uom_line_id.uom_id.name or '',
                    'qty': move.multi_uom_qty or '0',
                    'deliver_qty': move.multi_quantity_done or '0',
                    'balance_qty': balance_qty or '0',
                    'ratio_remark': move.uom_ratio_remark or '',
                })
                balance_qty = 0
                no += 1

            records.append({
                'image': order.company_id.logo or '',
                'name': order.name or '',
                'vol_no': order.origin or '',
                'customer_id': order.partner_id.name or '',
                'purchaser': order.purchaser_id.name or '',
                'remark': order.remark or '',
                'printed_date': print_date.strftime('%d-%m-%Y %I:%M:%S %p'),
                'effective_date': order.scheduled_date.strftime('%d-%m-%Y') or '',
                'total_qty_done': total_qty_done or '0',
                'move_ids_without_package': move_ids_without_package,
                'report_template_id': report_template_id,
                'branch': order.picking_type_id.warehouse_id.name,
            })
        return self.env.ref('report_form.action_grn_b5_pdf_report').report_action(self, data={
            'records': records,
        })
