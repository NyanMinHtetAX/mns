import werkzeug
import json
from dateutil.relativedelta import relativedelta

from odoo import http, fields
from odoo.http import request
from functools import wraps
from odoo.addons.web.controllers.main import Session
from odoo import SUPERUSER_ID
from datetime import datetime, date
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT
from odoo.osv import expression
import logging

_logger = logging.getLogger(__name__)
from dateutil.relativedelta import relativedelta

HEADERS = [('content-type', 'application/json')]


def convert_to_multi_uom(product, qty):
    total_consumed_qty = 0
    multi_uom_qty = ''
    if product.multi_uom_line_ids:
        lines = product.multi_uom_line_ids
        lines = sorted(lines, key=lambda l: l.ratio, reverse=True)
        remaining_qty = qty
        for line in lines:
            if total_consumed_qty == qty:
                break
            converted_qty = remaining_qty / line.ratio
            if abs(converted_qty) >= 1:
                multi_uom_qty += f' {int(converted_qty)} {line.uom_id.name} '
                consumed_qty = int(converted_qty) * line.ratio
                remaining_qty -= consumed_qty
                total_consumed_qty += consumed_qty
    else:
        multi_uom_qty = f'{qty} {product.uom_id.name}'
    return multi_uom_qty


def rest_api_auth(f):
    @wraps(f)
    def wrapped(self, **kwargs):
        headers = request.httprequest.headers;
        if 'db' not in headers:
            return f(self, **kwargs)
        if request.session.db:
            self.db = request.session.db
        else:
            self.db = request.session.db = request.httprequest.headers.get('db')
        self.req_body = request.params
        self.auth_info = self.auth_api_user(**kwargs)
        self.api_user = request.api_user = self.auth_info.get('api_user')
        return f(self, **kwargs)

    return wrapped


class OdooRest(http.Controller):

    def _response(self, response, status_code=200):
        body = {}
        mime = 'application/json; charset=utf-8'
        try:
            body = json.dumps(response, default=lambda o: o.__dict__)
        except Exception as e:
            body['message'] = "ERROR: %r" % (e)
            body['success'] = False
            body = json.dumps(body, default=lambda o: o.__dict__)
        headers = [
            ('Content-Type', mime),
            ('Content-Length', len(body))
        ]
        return werkzeug.wrappers.Response(body, headers=headers, status=status_code)

    @http.route('/api/auth', type='http', auth='none', methods=['POST'], csrf=False)
    def login(self, **kwargs):
        params = request.params
        username = params.get('username')
        password = params.get('password')
        sale_team_code = params.get('sale_team_code')
        device_imei = params.get('device_imei')
        device_vals = json.loads(params.get('device_vals', '{}'))
        crm_data = request.env['crm.team'].sudo().search([('code', '=', sale_team_code)])
        
        if not (username and password and sale_team_code):
            return self._response({'success': False, 'error': 'Missing required parameters.'})
        member_length = len(crm_data.member_ids.ids)
        list_len = 0
        for rec in crm_data.member_ids:
            if rec.login == username:
                Session.authenticate({}, request.session.db, username, password)
                user = request.env.user
                login_device = request.env['mobile.device'].with_context(active_test=False).sudo().search(
                    [('device_imei', '=', device_imei),
                     ('device_imei', '!=', False)], limit=1)
                login_device_one = request.env['mobile.device'].sudo().search([])
                is_new_device = False
                if not login_device:
                    if not device_vals:
                        return self._response({'success': False,
                                               'error': 'There is no device with the given IMEI. You have to give the device values to create a new device.'})
                    else:
                        device_vals['device_imei'] = device_imei
                        for data in login_device_one:
                            if data.sale_team_id.id == crm_data.id:
                                return self._response({'success': False,
                                                       'error': 'Sale team is already logged in another device'})

                        login_device = request.env['mobile.device'].sudo().create(device_vals)
                        login_device.company_id = user.company_id
                        is_new_device = True
                elif login_device:
                    if login_device.sale_team_id.id != crm_data.id:
                        return self._response({'success': False,
                                               'error': 'Device with the given IMEI is already in another sale team.'})
                    if (not login_device.active or login_device.state != 'approve'):
                        return self._response({'success': False,
                                               'error': 'Device with the given IMEI is either archived or has not been approved yet.'})

                tokenKey = str(datetime.today())
                jwt_token = request.session.sid
                template_data = request.env['custom.report.template'].sudo().search([('company_name','=',user.company_id.name)])
                
                return self._response({
                    'success': True,
                    'message': 'Successfully logged in.',
                    'token': tokenKey,
                    'jwt_token': jwt_token,
                    'user_id': user.id,
                    'user_name': user.name,
                    'device_id': login_device.id,
                    'device_name': login_device.name or '',
                    'is_new_device': is_new_device,
                    'company_id': user.company_id.id,
                    'company_name': user.company_id.name,
                    'company_image': template_data.image_1920.decode('utf-8') or '',
                    'title1': template_data.title1,
                    'title2': template_data.title2,
                    'address': template_data.address,
                    'company_phone': template_data.company_phone,
                    'social_viber': template_data.social_viber,
                    'social_mail': template_data.social_mail,
                    'footer': template_data.footer,
                    'note': template_data.note,
                    'phone': template_data.phone,
                    'mobile': template_data.mobile,
                    'thank': template_data.thank,
                    'remark_note': template_data.remark_note,
                    'other_phone': template_data.other_phone,
                    'service_phone': template_data.service_phone,
                    'product_group_ids': crm_data.product_group_ids.ids,
                    'image': user.image_1920 and user.image_1920.decode('utf-8') or '',
                    'partner_id': user.partner_id.id,
                    'company_currency_id': user.company_id.currency_id.id,
                    'company_currency_name': user.company_id.currency_id.name,
                })
            else:
                list_len += 1
            if list_len == member_length:
                sale_team_name = request.env['crm.team'].sudo().search([('code','=',sale_team_code)])
                return self._response({'success': False,'error': 'Current account does not exist in '+ sale_team_name.name+'!'})

    @http.route('/check/device', type='json', auth='none', methods=['POST'], csrf=False)
    def check_device_state(self):
        device_id = request.jsonrequest.get('device_id', )
        sale_team_id = request.jsonrequest.get('sale_team_id')
        device = request.env['mobile.device'].sudo().search(
            [('id', '=', device_id), ('sale_team_id', '=', sale_team_id)])
        if device:
            return {'state': device.state}
        else:
            return {'state': 'reject'}

    @staticmethod
    def auth_api_user(**kwargs):
        token = request.httprequest.headers.get('authorization')
        api_user = request.api_user = request.env['api.user'].check_token(token)
        return api_user

    # Create Methods
    @http.route('/customer/createCustomer', type='json', auth='none', methods=['POST'], csrf=False)
    def createCustomer(self, **kwargs):
        customers_values = request.jsonrequest['values']
        user = request.env['res.users'].sudo().browse(request.session.uid)
        uid = request.session.uid
        if not uid:
            return {'success': False, 'error': 'Invalid cookie.'}
        customer_ids = []

        available_fields = request.env['res.partner'].fields_get_keys()
        data = request.env['product.pricelist'].sudo().search([])
        stock_location_data = request.env['stock.location'].sudo().search([('usage', '=', 'customer')])

        for values in customers_values:
            vals = {
                'name': values['name'],
                'image_1920': values['image_1920'],
                'street': values['street'],
                'street2': values['street2'],
                'phone': values['phone'],
                'mobile': values['mobile'],
                'email': values['email'],
                'latitude': float(values['latitude']),
                'longitude': float(values['longitude']),
                'township_id': int(values['township_id']),
                'x_city_id': int(values['x_city_id']),
                'state_id': int(values['state_id']),
                'outlet_type': int(values['outlet_type']),
                'sale_channel_ids': [(6, 0, values['sale_channel_ids'])],
                'property_payment_term_id': values['property_payment_term_id'],
                'property_stock_customer': stock_location_data[0].id or False,
                'property_product_pricelist': values['property_product_pricelist'] or False,
                'pricelist_ids': [(0,0,values['pricelist_ids'])],
                'customer': False,
                'is_mobile_customer': True,
                'company_id': user.company_id.id,
            }
            print('vals', vals)
            for field in values:
                if field in available_fields:
                    vals[field] = values[field]
            customer = request.env['res.partner'].sudo().with_company(user.company_id.id).create(vals)
            customer.update({
                'property_stock_customer': stock_location_data[0].id or False,
            })
            customer_ids.append(customer.id)

        return {'success': True, 'message': 'Customer created successfully.', 'created_ids': customer_ids}

    @http.route('/visitReport/createVisitReport', type='json', auth='none', methods=['POST'], csrf=False)
    def createVisitReport(self, **kwargs):
        values = request.params
        user = request.env['res.users'].sudo().browse(request.session.uid)
        uid = request.session.uid
        if not uid:
            return {'success': False, 'error': 'Invalid cookie.'}
        company_id = user.company_id.id
        request.env.company = user.company_id
        request.env.user = user
        vals = {'company_id': company_id}
        available_fields = request.env['visit.report'].fields_get_keys()
        for field in values:
            if field in available_fields:
                vals[field] = values[field]
        visitReport = request.env['visit.report'].sudo().create(vals)
        for attachment in values['images']:
            request.env['visit.report.image'].sudo().create({
                'name': attachment['name'],
                'image': attachment['datas'],
                'image_id': visitReport.id,
            })
        return {'success': True, 'message': 'Visit Report created successfully.', 'created_id': visitReport.id}

    @http.route('/stockRequest/createStockRequest', type='json', auth='none', methods=['POST'], csrf=False)
    def createStockRequest(self, **kwargs):
        values = request.params
        user = request.env['res.users'].sudo().browse(request.session.uid)
        uid = request.session.uid
        if not uid:
            return {'success': False, 'error': 'Invalid cookie.'}
        company_id = user.company_id.id
        request.env.company = user.company_id
        request.env.user = user
        location = request.env['stock.location'].with_user(SUPERUSER_ID).browse(values['location_id'])
        picking_type_id = location.warehouse_id.int_type_id.id
        available_fields = request.env['stock.picking'].sudo().fields_get_keys()
        team_data = request.env['crm.team'].sudo().search([('id', '=', values['team_id'])])
        vals = {
            'location_id': values['location_id'],
            'location_dest_id': values['location_dest_id'],
            'team_id': values['team_id'],
            'analytic_account_id': team_data.analytic_account_id.id,
            'user_id': values['user_id'],
            'picking_type_id': picking_type_id,
            'origin': values['mobileSRRef'],
        }
        for field in values:
            if field in available_fields:
                vals[field] = values[field]
        stockRequest = request.env['stock.picking'].with_user(SUPERUSER_ID).with_company(company_id).create(vals)

        for stock in values['stockLineList']:
            multi_uom_line = request.env['multi.uom.line'].with_user(SUPERUSER_ID).browse(stock['multi_uom_line_id'])
            product_qty = float(stock['qty']) * multi_uom_line.ratio
            if stock.get('lot_id'):
                stockMove = request.env['stock.move'].with_user(SUPERUSER_ID).with_company(company_id).create({
                    'name': stock['completeName'],
                    'picking_id': stockRequest.id,
                    'product_id': stock['product_id'],
                    'product_uom': stock['uom_id'],
                    'multi_uom_qty': float(stock['qty']),
                    'product_uom_qty': product_qty,
                    'location_id': values['location_id'],
                    'location_dest_id': values['location_dest_id'],
                    'multi_uom_line_id': stock['multi_uom_line_id'],
                    'lot_ids': [(4, stock.get('lot_id'))],
                })
            else:
                stockMove = request.env['stock.move'].with_user(SUPERUSER_ID).with_company(company_id).create({
                    'name': stock['completeName'],
                    'picking_id': stockRequest.id,
                    'product_id': stock['product_id'],
                    'product_uom': stock['uom_id'],
                    'multi_uom_qty': float(stock['qty']),
                    'product_uom_qty': product_qty,
                    'location_id': values['location_id'],
                    'location_dest_id': values['location_dest_id'],
                    'multi_uom_line_id': stock['multi_uom_line_id'],
                })
        return {'success': True, 'message': 'Stock Line created successfully.', 'created_id': stockRequest.id,
                'picking_No': stockRequest.name}

    @http.route('/daily-sale/create', type='json', auth='none', methods=['POST'], csrf=False)
    def create_daily_sale(self, **kwargs):

        params = request.jsonrequest
        uid = request.session.uid
        user = request.env['res.users'].sudo().browse(uid)
        company_id = user.company_id.id
        if not uid:
            return {'success': False, 'error': 'Invalid cookie.'}
        analytic_account_id = request.env['crm.team'].sudo().browse(
            params['team_id']).analytic_account_id.id
        values = {
            'team_id': params['team_id'],
            'sales_man': params['user_id'],
            'route_plan_id': params['route_plan_id'],
            'analytic_account_id': analytic_account_id,
            'date': fields.Date.context_today(request),
            'company_id': company_id,
        }
        available_fields = request.env['daily.sale.summary'].sudo().fields_get_keys()
        for field in params:
            if field in available_fields:
                values[field] = params[field]
        daily_sale_summary = request.env['daily.sale.summary'].with_user(SUPERUSER_ID).create(values)
        return {'success': True, 'daily_sale_summary_id': daily_sale_summary.id, 'ref': daily_sale_summary.name}

    @http.route('/api/action/daily-sale-summary/close', type='json', auth='none', methods=['POST'], csrf=False)
    def action_daily_sale_summary_close(self, **kwargs):
        params = request.jsonrequest
        uid = request.session.uid
        if not uid:
            return {'success': False, 'error': 'Invalid cookie.'}
        request.env['daily.sale.summary'].with_user(SUPERUSER_ID).browse(params['record_id']).action_close()
        return {'success': True}

    @http.route('/van/order/create', type='json', auth='none', methods=['POST'], csrf=False)
    def create_van_order(self, **kwargs):
        values = request.jsonrequest
        uid = int(request.httprequest.headers.get('uid'))
        if not uid:
            return {'success': False, 'error': 'Invalid cookie.'}
        company = request.env['res.users'].sudo().browse(SUPERUSER_ID).company_id
        warehouse_id = request.env['stock.location'].with_user(SUPERUSER_ID).browse(
            values['location_id']).warehouse_id.id
        analytic_account_id = request.env['daily.sale.summary'].with_user(SUPERUSER_ID).browse(
            values['daily_sale_summary_id']).analytic_account_id.id

        order_vals = {
            'date': values['date'],
            'partner_id': values['partner_id'],
            'warehouse_id': warehouse_id,
            'location_id': values['location_id'],
            'fleet_id': values['fleet_id'],
            'team_id': values['team_id'],
            'pricelist_id': values['pricelist_id'],
            'daily_sale_summary_id': values['daily_sale_summary_id'],
            'state': values['state'],
            'analytic_account_id': analytic_account_id,
            'company_id': company.id,
        }
        order_fields = request.env['van.order'].with_user(SUPERUSER_ID).fields_get_keys()
        order_line_fields = request.env['van.order.line'].with_user(SUPERUSER_ID).fields_get_keys()
        for order_field in values:
            if order_field in order_fields:
                order_vals[order_field] = values[order_field]
        order = request.env['van.order'].with_user(uid).with_company(company.id).sudo().create(order_vals)
        lines_to_create = []
        order_lines = values.get('order_lines', [])
        for line in order_lines:
            multi_uom_line = request.env['multi.uom.line'].sudo().browse(line.get('multi_uom_line_id'))
            product_qty = line.get('qty') * multi_uom_line.ratio
            line_vals = {
                'name': line.get('description', False),
                'product_id': line.get('product_id', False),
                'qty': line.get('qty', 0),
                'product_uom_qty': product_qty,
                'uom_id': line.get('uom_id', False),
                'price_unit': line.get('price_unit', 0),
                'tax_ids': [(6, 0, line.get('tax_ids', []))],
                'order_id': order.id,
            }
            for order_line_field in line:
                if order_line_field in order_line_fields:
                    line_vals[order_line_field] = line[order_line_field]
            lines_to_create.append(line_vals)
        request.env['van.order.line'].with_user(uid).sudo().create(lines_to_create)

        payments_to_create = []
        payment_lines = values.get('payment_lines', [])
        for line in payment_lines:
            payments_to_create.append({
                'date': datetime.now(),
                'payment_method_id': line.get('payment_method_id', False),
                'amount': line.get('amount', 0),
                'currency_id': line.get('currency_id', False),
                'order_id': order.id,
            })
        request.env['van.order.payment'].with_user(uid).sudo().create(payments_to_create)

        order_str = "SO/" + str(date.today().year) + "/" + str(date.today().month) + "/" + str(
            date.today().day) + "/" + str(order.id)
        order.write({
            "order_reference": order_str
        })
        if values['consignment'] == True:
            return {'success': 1, 'order_id': order.id}
        else:
            return {'success': 1, 'order_id': order_str}

    @http.route('/api/create/sale-order', type='json', auth='none', methods=['POST'], csrf=False)
    def create_pre_sale_order(self, **kwargs):
        params = request.jsonrequest
        uid = request.session.uid
        if not uid:
            return {'success': False, 'error': 'Invalid cookie.'}
        company_id = request.env['res.users'].sudo().browse(uid).company_id.id
        warehouse_id = request.env['stock.warehouse'].sudo().search([('company_id', '=', company_id)], limit=1)

        values = {
            'partner_id': params.get('partner_id', False),
            'partner_invoice_id': params.get('partner_invoice_id', False),
            'partner_shipping_id': params.get('partner_shipping_id', False),
            'date_order': params.get('date_order', False),
            'pricelist_id': params.get('pricelist_id', False),
            'currency_id': params.get('currency_id', False),
            'payment_term_id': params.get('payment_term_id', False),
            'warehouse_id': warehouse_id,
            'user_id': params.get('user_id', False),
            'sale_type': 'pre_order',
        }
        available_fields = request.env['sale.order'].fields_get_keys()
        available_line_fields = request.env['sale.order.line'].fields_get_keys()
        for field in params:
            if field in available_fields:
                values[field] = params[field]
        company_id = request.env['res.users'].sudo().browse(uid).company_id.id
        order_lines = []
        for product in params['products']:
            multi_uom_line = request.env['multi.uom.line'].sudo().browse(product['multi_uom_line_id'])
            product_qty = product['qty'] * multi_uom_line.ratio
            product_price_unit = product['price_unit'] / multi_uom_line.ratio
            product_discount = product.get('discount', 0) / multi_uom_line.ratio
            line_vals = {
                'name': product['name'],
                'product_id': product['product_id'],
                'multi_uom_qty': product['qty'],
                'product_uom_qty': product_qty,
                'product_uom': product['uom_id'],
                'multi_price_unit': product['price_unit'],
                'multi_uom_discount': product.get('discount', 0),
            }
            for line_field in product:
                if line_field in available_line_fields:
                    line_vals[line_field] = product[line_field]
            line_vals.update({
                'price_unit': product_price_unit,
                'discount': product_discount,
            })
            order_lines.append((0, 0, line_vals))
        values['order_line'] = order_lines
        values['warehouse_id'] = warehouse_id.id
        order = request.env['sale.order'].with_company(company_id).sudo().create(values)

        order.write({
            "client_order_reference": "SO-" + str(order.id)
        })
        return {'success': True, 'order_id': order.id}

    @http.route('/api/create/payment-collection', type='json', auth='none', methods=['POST'], csrf=False)
    def create_payment_collection(self, **kwargs):
        params = request.jsonrequest
        uid = request.session.uid
        if not uid:
            return {'success': False, 'error': 'Invalid cookie.'}
        user = request.env['res.users'].sudo().browse(uid)
        company_id = user.company_id.id
        if not uid:
            return {'success': False, 'error': 'Invalid cookie.'}
        # Creating Parent
        values = {'company_id': company_id}
        available_fields = request.env['payment.collection'].fields_get_keys()
        for field in params:
            if field in available_fields:
                values[field] = params[field]
        payment_collection = request.env['payment.collection'].with_user(uid).sudo().create(values)
        payment_collection.write({
            "salesman_signature": params['salesman_signature'],
            "salesman_signed_by": params['salesman_signed_by'],
            "salesman_signed_on": params['salesman_signed_on'],
            })

        # Creating Child [Invoice]
        invoice_lines_to_create = []
        invoice_lines = params['invoice_lines']
        available_fields = request.env['payment.collection.line'].fields_get_keys()
        for invoice in invoice_lines:
            invoice_vals = {'collection_id': payment_collection.id}
            for field in invoice:
                if field in available_fields:
                    invoice_vals[field] = invoice[field]
            invoice_lines_to_create.append(invoice_vals)
        request.env['payment.collection.line'].with_user(uid).sudo().create(invoice_lines_to_create)

        # Creating Child [Payment]
        payments_lines_to_create = []
        payment_lines = params['payment_lines']
        available_fields = request.env['payment.collection.payment.line'].fields_get_keys()
        for payment in payment_lines:
            payment_vals = {'payment_collection_id': payment_collection.id}
            for field in payment:
                if field in available_fields:
                    payment_vals[field] = payment[field]
            payments_lines_to_create.append(payment_vals)
        request.env['payment.collection.payment.line'].with_user(uid).sudo().create(payments_lines_to_create)
        return {
            'record_id': payment_collection.id,
            'invoice_line_ids': [{'invoice_id': line.invoice_id.id, 'line_id': line.id} for line in
                                 payment_collection.line_ids]
        }

    @http.route('/api/create/payment-collection-line', type='json', auth='none', methods=['POST'], csrf=False)
    def create_payment_collection_line(self, **kwargs):
        params = request.jsonrequest
        uid = request.session.uid
        if not uid:
            return {'success': False, 'error': 'Invalid cookie.'}
        invoice_lines_to_create = []
        invoice_lines = params['invoice_lines']
        available_fields = request.env['payment.collection.line'].fields_get_keys()
        for invoice in invoice_lines:
            invoice_vals = {}
            for field in invoice:
                if field in available_fields:
                    invoice_vals[field] = invoice[field]
            invoice_lines_to_create.append(invoice_vals)
        lines = request.env['payment.collection.line'].with_user(uid).sudo().create(invoice_lines_to_create)
        
        return {'record_ids': lines.ids}

    @http.route('/api/create/payment-collection-payment-line', type='json', auth='none', methods=['POST'], csrf=False)
    def create_payment_collection_payment_line(self, **kwargs):
        params = request.jsonrequest
        uid = request.session.uid
        if not uid:
            return {'success': False, 'error': 'Invalid cookie.'}
        payments_lines_to_create = []
        payment_lines = params['payment_lines']
        daily_sale_summary_id = params['daily_sale_summary']
        available_fields = request.env['payment.collection.payment.line'].fields_get_keys()
        for payment in payment_lines:
            payment_vals = {}
            for field in payment:
                if field in available_fields:
                    payment_vals[field] = payment[field]
            payments_lines_to_create.append(payment_vals)
        lines = request.env['payment.collection.payment.line'].with_user(uid).sudo().create(payments_lines_to_create)
        lines.payment_collection_id.daily_sale_summary_id = daily_sale_summary_id
        return {'record_ids': lines.ids}

    @http.route('/api/create/payment-collection-one-payment-line', type='json', auth='none', methods=['POST'], csrf=False)
    def create_payment_collection_one_payment_line(self, **kwargs):
        params = request.jsonrequest
        uid = request.session.uid
        if not uid:
            return {'success': False, 'error': 'Invalid cookie.'}
        payments_lines_to_create = []
        payment_lines = params['payment_lines']
        daily_sale_summary_id = params['daily_sale_summary']
        available_fields = request.env['payment.collection.one.payment.line'].fields_get_keys()
        for payment in payment_lines:
            payment_vals = {}
            for field in payment:
                if field in available_fields:
                    payment_vals[field] = payment[field]
            payments_lines_to_create.append(payment_vals)
        lines = request.env['payment.collection.one.payment.line'].with_user(uid).sudo().create(payments_lines_to_create)
        
        lines.payment_collection_id.daily_sale_summary_id = daily_sale_summary_id 
        return {'record_ids': lines.ids}

    @http.route('/api/action/payment-collection/confirm', type='json', auth='none', methods=['POST'], csrf=False)
    def action_payment_collection_confirm(self, **kwargs):
        params = request.jsonrequest
        uid = request.session.uid
        if not uid:
            return {'success': False, 'error': 'Invalid cookie.'}
        request.env['payment.collection'].with_user(SUPERUSER_ID).browse(params['record_id']).btn_confirm()
        return {'success': True}

    @http.route('/api/action/payment-collection/approve', type='json', auth='none', methods=['POST'], csrf=False)
    def action_payment_collection_approve(self, **kwargs):
        params = request.jsonrequest
        uid = request.session.uid
        if not uid:
            return {'success': False, 'error': 'Invalid cookie.'}
        request.env['payment.collection'].with_user(SUPERUSER_ID).browse(params['record_id']).write({
            'signature': params['signature'],
            'signed_by': params['signed_by'],
            'signed_on': params['signed_on'],
            'slip_image': params['slip_image'],
            "salesman_signature": params['salesman_signature'],
            "salesman_signed_by": params['salesman_signed_by'],
            "salesman_signed_on": params['salesman_signed_on'],
            "mobile_ref": params['mobile_ref'],
        })
        request.env['payment.collection'].with_user(SUPERUSER_ID).browse(params['record_id']).btn_approve()
        return {'success': True}

    @http.route('/api/action/payment-collection-one/approve', type='json', auth='none', methods=['POST'], csrf=False)
    def action_payment_collection_one_approve(self, **kwargs):
        params = request.jsonrequest
        uid = request.session.uid
        if not uid:
            return {'success': False, 'error': 'Invalid cookie.'}
        request.env['payment.collection.one'].with_user(SUPERUSER_ID).browse(params['record_id']).write({
            'signature': params['signature'],
            'signed_by': params['signed_by'],
            'signed_on': params['signed_on'],
            'slip_image': params['slip_image'],
            'mobile_ref': params['mobile_ref'],
            "salesman_signature": params['salesman_signature'],
            "salesman_signed_by": params['salesman_signed_by'],
            "salesman_signed_on": params['salesman_signed_on'],
        })
        request.env['payment.collection.one'].with_user(SUPERUSER_ID).browse(params['record_id']).btn_approve()
        return {'success': True}

    @http.route('/api/action/payment-collection/apply-payment', type='json', auth='none', methods=['POST'], csrf=False)
    def action_apply_payment(self, **kwargs):

        params = request.jsonrequest
        uid = request.session.uid
        if not uid:
            return {'success': False, 'error': 'Invalid cookie.'}
        line = request.env['payment.collection.line'].with_user(SUPERUSER_ID).browse(params['record_id'])
        if 'amount_paid' in params:
            if params['amount_paid'] > 0:
                line.write({'amount_paid': params['amount_paid']})
        line.btn_apply_payment()
        return {'success': True}

    @staticmethod
    def _get_product_lot(product_id, lot):
        domain = [('product_id', '=', product_id), ('name', '=', lot)]
        stock_lot = request.env['stock.production.lot'].with_user(SUPERUSER_ID).search(domain)
        if not stock_lot:
            return {'missing': True, 'message': f'Lot({lot}) is missing.'}
        return {'lot_id': stock_lot.id}

    @http.route('/api/create/stock-transfer', type='json', auth='none', methods=['POST'], csrf=False)
    def create_stock_transfer(self, **kwargs):
        params = request.jsonrequest
        uid = request.session.uid
        if not uid:
            return {'success': False, 'error': 'Invalid cookie.'}
        user = request.env['res.users'].sudo().browse(uid)
        company_id = user.company_id.id
        if not uid:
            return {'success': False, 'error': 'Invalid cookie.'}
        move_lines = []
        moves = params['products']
        location_id = params['picking_values']['location_id']
        location_dest_id = params['picking_values']['location_dest_id']
        picking_type_id = request.env['stock.location'].with_user(SUPERUSER_ID).browse(
            location_id).warehouse_id.int_type_id.id
        params['picking_values'].update({
            'picking_type_id': picking_type_id,
            'company_id': company_id,
            'is_van_transfer': True,
        })
        picking = request.env['stock.picking'].with_user(uid).sudo().create(params['picking_values'])
        for move in moves:
            multi_uom_line = request.env['multi.uom.line'].with_user(SUPERUSER_ID).browse(move['multi_uom_line_id'])
            product_qty = multi_uom_line.ratio * move['multi_uom_qty']
            move.update({
                'picking_id': picking.id,
                'product_uom_qty': product_qty,
                'quantity_done': product_qty,
                'location_id': location_id,
                'location_dest_id': location_dest_id,
            })
            move_lines.append({
                'product_id': move['product_id'],
                'product_uom_qty': move['product_uom_qty'],
                'multi_uom_qty': move['multi_uom_qty'],
                'qty_done': move['product_uom_qty'],
                'product_uom_id': move['product_uom'],
                'multi_uom_line_id': move['multi_uom_line_id'],
                'lot_id': move.get('lot_id'),
                'location_id': location_id,
                'location_dest_id': location_dest_id,
                'picking_id': picking.id,
                'company_id': company_id,
            })
        request.env['stock.move'].with_user(uid).sudo().create(moves)
        # request.env['stock.move.line'].with_user(uid).create(move_lines)
        picking.action_confirm()
        picking._action_done()
        return {'result': 'success', 'record_id': picking.id}

    @http.route('/api/create/stock-scrap', type='json', auth='none', methods=['POST'], csrf=False)
    def create_stock_scrap(self, **kwargs):
        params = request.jsonrequest
        uid = request.session.uid
        if not uid:
            return {'success': False, 'error': 'Invalid cookie.'}
        values = {
            'document_number': params['document_number'],
            'excepted_date': params['expected_date'],
            'sale_man_id': params['sale_man_id'],
            'team_id': params['team_id'],
            'is_van_scrap': True,
        }
        available_fields = request.env['stock.multi.scrap'].sudo().fields_get_keys()
        for field in params:
            if field in available_fields:
                values[field] = params[field]
        scrap = request.env['stock.multi.scrap'].with_user(uid).sudo().create(values)
        lines = params['products']
        scrap_lines = []
        available_fields = request.env['stock.multi.scrap.line'].sudo().fields_get_keys()
        for line in lines:
            line_vals = {
                'multi_scrap_id': scrap.id,
            }
            for field in line:
                if field in available_fields:
                    line_vals[field] = line[field]
            multi_uom_line = request.env['multi.uom.line'].with_user(SUPERUSER_ID).browse(
                line_vals['multi_uom_line_id'])
            line_vals['scrap_qty'] = multi_uom_line.ratio * line_vals['multi_uom_qty']
            scrap_lines.append(line_vals)

        request.env['stock.multi.scrap.line'].with_user(uid).sudo().create(scrap_lines)
        return {'success': True, 'record_id': scrap.id, 'ref': scrap.name}

    @http.route('/api/create/sale-stock-return', type='json', auth='none', methods=['POST'], csrf=False)
    def create_sale_stock_return(self):
        params = request.jsonrequest
        uid = request.session.uid
        user = request.env['res.users'].sudo().browse(uid)
        company_id = user.company_id.id
        van_order_ref = params['order_ref']
        daily_sale_summary_id = params['session_id']
        van_order_id = request.env['van.order'].sudo().search([('order_reference','=',van_order_ref)])
        if not uid:
            return {'error': 'Invalid cookie.'}
        analytic_account_id = request.env['crm.team'].sudo().browse(
            params['team_id']).analytic_account_id.id
        values = {
            'analytic_account_id': analytic_account_id,
            'company_id': company_id,
        }
        available_fields = request.env['sale.stock.return'].sudo().fields_get_keys()
        for field in params:
            if field in available_fields:
                values[field] = params[field]
        values.update({
            'description': params['description'],
            'order_ref': van_order_id.id,
            'daily_sale_summary_id': daily_sale_summary_id
        })
        sale_stock_return = request.env['sale.stock.return'].with_user(uid).sudo().create(values)

        available_fields = request.env['sale.stock.return.line'].fields_get_keys()
        lines = []
        for product in params['products']:
            vals = {'sale_stock_return_id': sale_stock_return.id}
            for field in product:
                if field in available_fields:
                    vals[field] = product[field]
            lines.append(vals)
        request.env['sale.stock.return.line'].with_user(uid).sudo().create(lines)

        images = []
        for image in params['images']:
            images.append({
                'name': image['name'],
                'image': image['image'],
                'sale_stock_return_id': sale_stock_return.id
            })
        request.env['sale.stock.return.image'].with_user(uid).sudo().create(images)

        payments_to_create = []
        payment_lines = params['payment_lines']
        for line in payment_lines:
            payments_to_create.append({
                'date': datetime.now(),
                'payment_method_id': line.get('payment_method_id', False),
                'amount': line.get('amount', 0),
                'currency_id': line.get('currency_id', False),
                'return_id': sale_stock_return.id,
                'daily_sale_summary_id': daily_sale_summary_id
            })
        request.env['sale.return.payment'].with_user(uid).sudo().create(payments_to_create)
        return {'success': True, 'record_id': sale_stock_return.id, 'ref': sale_stock_return.name}

    @http.route('/api/create/visit-attendance', type='json', auth='none', methods=['POST'], csrf=False)
    def create_visit_attendance(self):
        params = request.jsonrequest
        uid = request.session.uid
        user = request.env['res.users'].sudo().browse(uid)
        company_id = user.company_id.id
        if not uid:
            return {'success': False, 'error': 'Invalid cookie.'}
        values = {'company_id': company_id}
        available_fields = request.env['fs.visit.attendance'].sudo().fields_get_keys()
        for field in params:
            if field in available_fields:
                values[field] = params[field]
        visit_attendance = request.env['fs.visit.attendance'].with_user(SUPERUSER_ID).create(values)
        return {'success': True, 'record_id': visit_attendance.id}

    @http.route('/api/create/expense', type='json', auth='none', methods=['POST'], csrf=False)
    def create_expense(self):
        params = request.jsonrequest
        uid = request.session.uid
        user = request.env['res.users'].sudo().browse(uid)

        company_id = user.company_id.id
        currency_id = user.company_id.currency_id.id
        attachments = params.get('attachments', [])
        if not uid:
            return {'success': False, 'error': 'Invalid cookie.'}
        partner_id = params['employee_id']
        sale_team_id = request.env['crm.team'].sudo().browse(params['sale_team_id'])
        analytic_account_id = sale_team_id.analytic_account_id.id

        employee_id = False
        if partner_id:
            employee_id = request.env['hr.employee'].sudo().search([('user_id', '=', partner_id)])
        values = {
            'name': params['name'],
            'product_id': params['product_id'],
            'unit_amount': params['unit_amount'],
            'total_amount': params['total_amount'],
            'date': params['date'],
            'employee_id': employee_id.id,
            'payment_mode': params['payment_mode'],
            'company_id': company_id,
            'currency_id': currency_id,
            'description': params['description'],
            'reference': params['reference'],
            'analytic_account_id': analytic_account_id or 0,
        }
        state = params['state']
        expense = request.env['hr.expense'].sudo().create(values)
        if state:
            expense.write({
                'state': state
            })
        if attachments:
            expense.write({
                "attachment_image_ids": attachments
            })
        return {'success': True, 'expense_id': expense.id,
                'message': 'Expense Create Successful'
                }

    # Write Methods
    @http.route('/customer/updateCustomer', type='json', auth='none', methods=['POST'], csrf=False)
    def updateCustomer(self, **kwargs):
        values = request.params
        uid = request.session.uid
        if not uid:
            return {'success': False, 'error': 'Invalid cookie.'}
        user = request.env['res.users'].sudo().browse(uid)
        request.env.company = user.company_id
        request.env.user = user
        request.env['res.partner'].with_user(SUPERUSER_ID).browse(values['id']).with_company(user.company_id.id).write({
            'phone': values['phone'] or '',
            'mobile': values['mobile'] or '',
            'latitude': float(values['latitude']),
            'longitude': float(values['longitude']),
        })

        return {'success': True, 'message': 'Customer is updated successfully.'}

    @http.route('/api/write/<string:model>/<int:record_id>', type='json', auth='none', methods=['POST'], csrf=False)
    def write_model_record(self, model, record_id, **kwargs):
        uid = request.session.uid
        if not uid:
            return self._response({'success': False, 'error': 'Invalid cookie.'}, status_code=400)
        values = request.jsonrequest
        request.env[model].with_user(SUPERUSER_ID).browse(record_id).write(values)
        return {'message': 'Successfully updated the record.'}

    # GET Methods

    @http.route('/api/get/expense', type='json', auth='none', methods=['GET', 'POST'], csrf=False)
    def get_expense(self, **kwargs):
        records = []
        param = request.jsonrequest
        uid = request.session.uid
        if not uid:
            return {'success': False, 'error': 'Invalid cookie.'}
        domain = param.get('domain', '[]')
        if domain:
            try:
                domain = eval(domain)
            except Exception as e:
                return {'success': False, 'message': 'Invalid domain!'}
        write_date_data = param.get('write_date', False)

        if write_date_data:
            date_time_obj = datetime.strptime(write_date_data, '%Y-%m-%d %H:%M:%S')
            write_date = (date_time_obj + relativedelta(seconds=1)).strftime(DEFAULT_SERVER_DATETIME_FORMAT)
            first_time = False
        else:
            first_time = True
        if first_time:
            expense_datas = request.env['hr.expense'].with_user(SUPERUSER_ID).search(domain)
        else:
            domain = expression.AND([domain, [('write_date', '>=', write_date)]])
            expense_datas = request.env['hr.expense'].with_user(SUPERUSER_ID).search(domain)
        for rec in expense_datas:

            attachments = []
            if rec.attachment_image_ids:
                for attachment in rec.attachment_image_ids:
                    attachments.append(attachment.image_1920 and attachment.image_1920.decode('utf-8') or '')
            records.append(
                {
                    'id': rec.id,
                    'date': rec.date or '',
                    'name': rec.name or '',
                    'product_id': rec.product_id.id or '',
                    'product_name': rec.product_id.name or '',
                    'total_amount': rec.total_amount or 0.00,
                    'unit_amount': rec.unit_amount or 0.00,
                    'employee_id': rec.employee_id.id or 0,
                    'employee_name': rec.employee_id.name or '',
                    'payment_mode': rec.payment_mode or '',
                    'description': rec.description or '',
                    'analytic_account_id': rec.analytic_account_id.id or 0,
                    'analytic_account_name': rec.analytic_account_id.name or '',
                    'state': rec.state or '',
                    'reference': rec.reference or '',
                    'attachments': attachments,
                    'write_date': rec.write_date or ''
                }
            )
        return records

    @http.route('/api/get/db-list', type='http', auth='none', methods=['GET'], csrf=False)
    def get_db_list(self, **kwargs):
        return self._response(http.db_list())

    @http.route('/api/get/<int:company_id>/<int:sale_team_id>/settings', type='http', auth='none', methods=['GET'],
                csrf=False)
    def get_company_settings(self, company_id, sale_team_id, **kwargs):
        company = request.env['res.company'].with_user(SUPERUSER_ID).browse(company_id)
        sale_team = request.env['crm.team'].with_user(SUPERUSER_ID).browse(sale_team_id)
        pricelist_mode = request.env['ir.config_parameter'].with_user(SUPERUSER_ID).get_param(
            'product.product_pricelist_setting')
        values = {
            'fs_usage_status': company.fs_usage_status or '',
            'fs_primary_color': company.fs_primary_color or '',
            'fs_secondary_color': company.fs_secondary_color or '',
            'fs_map_max_distance': company.fs_map_max_distance,
            'fs_map_api_key': company.fs_map_api_key or '',
            'fs_sms_api_key': company.fs_sms_api_key or '',
            'fs_onesignal_app_id': company.fs_onesignal_app_id or '',
            'fs_data_storage_period': company.fs_data_storage_period or '',
            'fs_use_tax': company.fs_use_tax,
            'sale_tax_id': company.account_sale_tax_id.id or 0,
            'sale_tax_name': company.account_sale_tax_id.name or '',
            'fs_payment_collection_assigned_type': company.fs_payment_collection_assigned_type or '',
            'pricelist_mode': pricelist_mode or '',
            'fs_van_storage': company.van_storage or '',
        }
        return self._response(values)

    @http.route('/product/template', type='http', auth='none', methods=['GET'], csrf=False)
    def get_product_templates(self, **kwargs):

        records = []
        domain = kwargs.get('domain', [])
        if domain:
            try:
                domain = eval(domain)
            except Exception as e:
                return {'success': False, 'message': 'Invalid domain!'}
        products = request.env['product.template'].with_user(SUPERUSER_ID).search(domain)

        for product in products:
            uom = []
            category = []
            if product.categ_id:
                category = [product.categ_id.id, product.categ_id.display_name]
            if product.uom_id:
                uom = [product.uom_id.id, product.uom_id.name]
            records.append({
                'id': product.id,
                'name': product.name or '',
                'image': product.image_1920 or '',
                'barcode': product.barcode or '',
                'cost': product.standard_price or 0.0,
                'internal_note': product.description.striptags() if product.description else '',
                'category': category,
                'list_price': product.list_price or 0.0,
                'sale_description': product.description_sale or '',
                'fs_description': product.fs_description or '',
                'internal_ref': product.default_code or '',
                'uom': uom,
                'write_date': product.write_date.strftime(DEFAULT_SERVER_DATETIME_FORMAT),
            })
        return self._response(records)

    @http.route('/product/product', type='json', auth='none', cors="*", methods=['POST'], csrf=False)
    def get_product_products(self, **kwargs):
        records = []
        params = request.jsonrequest
        domain = params.get('domain', '[]')
        only_products_on_hand = params.get('only_products_on_hand', False)
        if domain:
            try:
                domain = eval(domain)
            except Exception as e:
                return {'success': False, 'message': 'Invalid domain!'}
        location_id = params.get('location_id', 0)
        company_id = request.env['res.users'].sudo().browse(request.session.uid).company_id.id
        if location_id:
            products = request.env['product.product'].with_context(location=int(location_id)).with_user(
                SUPERUSER_ID).search(domain)
        else:
            products = request.env['product.product'].with_user(SUPERUSER_ID).search(domain)
        for product in products:
            uom = []
            multi_uom_list = []
            category = []
            if product.categ_id:
                category = [product.categ_id.id, product.categ_id.display_name]
            if product.uom_id:
                uom = [product.uom_id.id, product.uom_id.name]
            if product.multi_uom_line_ids:
                for rec in product.multi_uom_line_ids:
                    multi_uom_list.append({
                        'uom_id': rec.id,
                        'uom_name': rec.uom_id.name,
                        'ratio': rec.ratio,
                        'is_default_uom': rec.is_default_uom or False,
                        'remark': rec.remark or '',
                        'product_tmpl_id': product.product_tmpl_id.id
                    })
            if product.image_1920:
                image = product.image_1920.decode('utf-8')
            else:
                image = ''
            customer_taxes = []
            taxes = product.taxes_id
            for tax in taxes:
                customer_taxes.append({
                    'id': tax.id,
                    'name': tax.name,
                    'amount': tax.amount,
                    'price_include': tax.price_include,
                })
            if location_id:
                quants = request.env['stock.quant'].with_user(SUPERUSER_ID).search([('product_id', '=', product.id),('location_id', '=', location_id)])
            else:
                quants = request.env['stock.quant'].with_user(SUPERUSER_ID).search([('product_id', '=', product.id),
                                                                                    ('location_id.usage', '=',
                                                                                     'internal')])
            on_hand_qty = sum(quants.mapped('quantity'))

            if not only_products_on_hand:
                records.append({
                    'id': product.id,
                    'name': product.name or '',
                    'type': product.detailed_type or '',
                    'barcode': product.barcode or '',
                    'cost': product.standard_price or 0.0,
                    'internal_note': product.description.striptags() if product.description else '',
                    'category': category,
                    'list_price': product.list_price or 0.0,
                    'sale_description': product.description_sale or '',
                    'fs_description': product.fs_description or '',
                    'internal_ref': product.default_code or '',
                    'product_group_id': product.product_group_id.id or 0,
                    'product_group_name': product.product_group_id.name,
                    'uom': uom,
                    'product_tmpl_id': product.product_tmpl_id.id,
                    'on_hand': on_hand_qty,
                    'multi_uom_qty': convert_to_multi_uom(product, product.qty_available),
                    'taxes': customer_taxes,
                    'tracking': product.tracking or '',
                    'multi_uom_list': multi_uom_list,
                    'write_date': product.write_date.strftime(DEFAULT_SERVER_DATETIME_FORMAT),
                    'image': image,
                })
            else:
                if quants:
                    if product.detailed_type !='service' and product.id == quants.product_id.id:
                    
                        records.append({
                            'id': product.id,
                            'name': product.name or '',
                            'type': product.detailed_type or '',
                            'barcode': product.barcode or '',
                            'cost': product.standard_price or 0.0,
                            'internal_note': product.description.striptags() if product.description else '',
                            'category': category,
                            'list_price': product.list_price or 0.0,
                            'sale_description': product.description_sale or '',
                            'fs_description': product.fs_description or '',
                            'internal_ref': product.default_code or '',
                            'product_group_id': product.product_group_id.id,
                            'product_group_name': product.product_group_id.name,
                            'uom': uom,
                            'product_tmpl_id': product.product_tmpl_id.id,
                            'on_hand': on_hand_qty,
                            'multi_uom_qty': convert_to_multi_uom(product, product.qty_available),
                            'taxes': customer_taxes,
                            'tracking': product.tracking or '',
                            'multi_uom_list': multi_uom_list,
                            'write_date': product.write_date.strftime(DEFAULT_SERVER_DATETIME_FORMAT),
                            'image': image,
                        })
            
        return records

    @http.route('/api/get/on-hand', type='json', auth='none', methods=['POST'], csrf=False)
    def get_product_on_hand(self):
        records = []
        params = request.jsonrequest
        only_products_on_hand = params.get('only_products_on_hand', False)
        location_id = params.get('location_id', False)
        domain = params.get('domain', '[]')
        company_id = request.env['res.users'].browse(request.session.uid).company_id.id
        if domain:
            try:
                domain = eval(domain)
            except Exception as e:
                return {'success': False, 'message': 'Invalid domain!'}
        products = request.env['product.product'].with_user(SUPERUSER_ID).search(domain)
        for product in products:
            if location_id:
                locations = request.env['stock.location'].with_user(SUPERUSER_ID).search(
                    [('id', 'child_of', location_id)])
                quants = request.env['stock.quant'].with_user(SUPERUSER_ID).search([('product_id', '=', product.id),
                                                                                    (
                                                                                        'location_id', 'in',
                                                                                        locations.ids)])
            else:
                quants = request.env['stock.quant'].with_user(SUPERUSER_ID).search([('product_id', '=', product.id),
                                                                                    ('location_id.usage', '=',
                                                                                     'internal')])
            on_hand_qty = sum(quants.mapped('quantity'))
            if only_products_on_hand and on_hand_qty == 0:
                continue
            records.append({
                'product_id': product.id,
                'qty': on_hand_qty,
            })
        return records

    @http.route('/product/image', type='json', auth='none', methods=['POST'], csrf=False)
    def get_product_images(self, **kwargs):
        records = []
        params = request.jsonrequest
        domain = params.get('domain', '[]')
        if domain:
            try:
                domain = eval(domain)
            except Exception as e:
                return {'success': False, 'message': 'Invalid domain!'}
        products = request.env['product.product'].with_user(SUPERUSER_ID).search(domain)
        for product in products:
            if product.image_1920:
                image = product.image_1920.decode('utf-8')
            else:
                image = ''
            records.append({
                'id': product.id,
                'image': image,
            })
        return records

    @http.route('/api/check_session', type='json', auth='none', methods=['POST'], csrf=False)
    def check_session(self):
        records = []
        params = request.jsonrequest
        domain = params.get('domain', '[]')
        route_plan_id = params.get('route_plan_id')
        sale_team_id = params.get('sale_team_id')
        day = params.get('day')
        if domain:
            try:
                domain = eval(domain)
            except Exception as e:
                return {'success': False, 'message': 'Invalid domain!'}
        route_plan_data = request.env['route.plan.checkin'].with_user(SUPERUSER_ID).search([('route_plan_id','=',route_plan_id)])
        if not route_plan_data:
            request.env['route.plan.checkin'].with_user(SUPERUSER_ID).create({
            'route_plan_id': route_plan_id,
            'sale_team_id': sale_team_id,
            'day': day,
            'date': date.today(),
            'check_in': True
            })
        else:
            route_plan_data.check_in = True

    @http.route('/stock_location/stock_location', type='http', auth='none', methods=['GET', 'POST'], csrf=False)
    def get_stock_location(self, **kwargs):

        records = []
        domain = kwargs.get('domain', [])
        if domain:
            try:
                domain = eval(domain)
            except Exception as e:
                return {'success': False, 'message': 'Invalid domain!'}
        stock_location = request.env['stock.location'].with_user(SUPERUSER_ID).search(domain)
        for location in stock_location:
            records.append({
                'id': location.id,
                'name': location.name or '',
                'complete_name': location.complete_name or '',
                'location_id': location.id or 0,
                'write_date': location.write_date.strftime(DEFAULT_SERVER_DATETIME_FORMAT),
            })
        return self._response(records)

    @http.route('/uom/uom', type='http', auth='none', methods=['GET', 'POST'], csrf=False)
    def get_uom(self, **kwargs):
        records = []
        domain = kwargs.get('domain', [])
        if domain:
            try:
                domain = eval(domain)
            except Exception as e:
                return {'success': False, 'message': 'Invalid domain!'}
        uomList = request.env['uom.uom'].with_user(SUPERUSER_ID).search(domain)
        for uom in uomList:
            records.append({
                'id': uom.id,
                'name': uom.name or '',
                'category_id': uom.category_id.id or 0,
                'write_date': uom.write_date.strftime(DEFAULT_SERVER_DATETIME_FORMAT),
            })
        return self._response(records)

    @http.route('/api/get/customer', type='http', auth='none', methods=['GET'], csrf=False)
    def get_route_customers(self, **kwargs):
        records = []
        domain = kwargs.get('domain', [])
        if domain:
            try:
                domain = eval(domain)
            except Exception as e:
                return {'success': False, 'message': 'Invalid domain!'}
        route_plan_partner = request.env['route.plan'].with_user(SUPERUSER_ID).search([])
        route_plan_partners = []
        for rec in route_plan_partners.partner_ids:
            route_plan_partners.append(rec.partner_id.id)
        domain += [('id', 'in', route_plan_partners)]
        customers = request.env['res.partner'].with_user(SUPERUSER_ID).search(domain)
        for customer in customers:
            if customer.image_1920:
                image = customer.image_1920.decode('utf-8')
            else:
                image = ''
            records.append({
                'id': customer.id,
                'ref': customer.ref,
                'code': customer.code,
                'name': customer.name,
                'image': image,
                'street1': customer.street,
                'street2': customer.street2,
                'phone': customer.phone,
                'mobile': customer.mobile,
                'email': customer.email,
                'latitude': customer.latitude,
                'longitude': customer.longitude,
                'township': customer.township_id.id,
                'city': customer.x_city_id.id,
                'state': customer.state_id.id,
                'outlet': customer.outlet_type.id,
                'sale_channel': customer.sale_channel_ids.ids,
                'payment_term': customer.property_payment_term_id.id,
                'wh_location': customer.property_stock_customer.id,
                'invoice_amount': customer.total_invoiced or 0.0,
                'pricelist_id': customer.property_product_pricelist.id,
                'write_date': customer.write_date.strftime(DEFAULT_SERVER_DATETIME_FORMAT),
            })
        return self._response(records)

    @http.route('/customer/customer', type='json', auth='none', methods=['GET', 'POST'], csrf=False)
    def get_customer_customers(self, **kwargs):

        records = []
        params = request.jsonrequest

        company_id = request.env['res.users'].sudo().browse(request.session.uid).company_id.id
        domain = params.get('domain', '[]')
        if domain:
            try:
                domain = eval(domain)
            except Exception as e:
                return {'success': False, 'message': 'Invalid domain!'}
        
        write_date_data = params.get('write_date', False)
        write_date = False
        
        if write_date_data:
            date_time_obj = datetime.strptime(write_date_data, '%Y-%m-%d %H:%M:%S')
            write_date = (date_time_obj + relativedelta(seconds=1)).strftime(DEFAULT_SERVER_DATETIME_FORMAT)
            first_time = False
        else:
            first_time = True
        if first_time:
            crm_team = request.env['crm.team'].with_user(SUPERUSER_ID).search(domain)
        else:
            crm_team = request.env['crm.team'].with_user(SUPERUSER_ID).search(domain)
       
        for customer in crm_team.sudo().partner_ids:
            if write_date_data:
                customer = request.env['res.partner'].with_user(SUPERUSER_ID).search([('id','=',customer.id),('company_id','=',company_id),('write_date','>',write_date)])
            else:
                customer = request.env['res.partner'].with_user(SUPERUSER_ID).search([('id','=',customer.id),('company_id','=',company_id)])
            if customer:
                township = []
                outlet = []
                city = []
                state = []
                sale_channel = []
                payment_term = []
                wh_location = []
                product_pricelist_data = request.env['product.pricelist'].with_user(SUPERUSER_ID)._get_partner_pricelist_multi(customer.ids, company_id=customer.company_id.id)
                if product_pricelist_data:
                    customer.property_product_pricelist = product_pricelist_data.get(customer.id)
                if customer.township_id:
                    township = [customer.township_id.id]
                if customer.outlet_type:
                    outlet = [customer.outlet_type.id]
                if customer.x_city_id:
                    city = [customer.x_city_id.id]
                if customer.state_id:
                    state = [customer.state_id.id]
                if customer.sale_channel_ids:
                    sale_channel = customer.sale_channel_ids.ids

                # GET PAYMENT TERM ID
                res_id = 'res.partner,' + str(customer.id)
                domain = [('res_id', '=', res_id), ('name', '=', 'property_payment_term_id'),('company_id','=',company_id)]
                check_ir_property = request.env['ir.property'].sudo().search(domain)
                if check_ir_property:
                    payment_term_id = check_ir_property.value_reference
                    payment_term_model, payment_term_id = payment_term_id.split(',')
                    if payment_term_id:
                        payment_term = [request.env['account.payment.term'].sudo().browse(payment_term_id).id]
                if customer.property_stock_customer:
                    wh_location = [customer.property_stock_customer.id]
                if customer.image_1920:
                    image = customer.image_1920.decode('utf-8')
                else:
                    image = ''
                allow_price = ','.join(str(v) for v in customer.pricelist_ids.ids)
                records.append({
                    'id': customer.id,
                    'ref': customer.ref,
                    'code': customer.code,
                    'name': customer.name or '',
                    'image': image,
                    'street1': customer.street or '',
                    'street2': customer.street2 or '',
                    'phone': customer.phone or '',
                    'mobile': customer.mobile or '',
                    'email': customer.email or '',
                    'latitude': customer.latitude or 0.0,
                    'payment_type': customer.payment_type,
                    'longitude': customer.longitude or 0.0,
                    'township': township or '',
                    'city': city or '',
                    'state': state or '',
                    'outlet': outlet or '',
                    'sale_channel': sale_channel or '',
                    'payment_term': payment_term,
                    'wh_location': wh_location,
                    'invoice_amount': customer.total_invoiced or 0.0,
                    'credit_limit': customer.credit_limit,
                    'pricelist_id': customer.property_product_pricelist.id or 0,
                    'allow_pricelist': allow_price or '',
                    'write_date': customer.write_date.strftime(DEFAULT_SERVER_DATETIME_FORMAT),
                })
        return records


    @http.route('/route_plan/route_plan', type='http', auth='none', methods=['GET', 'POST'], csrf=False)
    def get_routePlan_routePlans(self):
        records = []
        param = request.params
        domain = param.get('domain', '[]')
        if domain:
            try:
                domain = eval(domain)
            except Exception as e:
                return {'success': False, 'message': 'Invalid domain!'}
        write_date_data = param.get('write_date', False)

        if write_date_data:
            date_time_obj = datetime.strptime(write_date_data, '%Y-%m-%d %H:%M:%S')
            write_date = (date_time_obj + relativedelta(seconds=1)).strftime(DEFAULT_SERVER_DATETIME_FORMAT)
            first_time = False
        else:
            first_time = True
        if first_time:
            route_plans = request.env['route.plan'].with_user(SUPERUSER_ID).search(domain)
        else:
            domain = expression.AND([domain, [('write_date', '>', write_date)]])
            route_plans = request.env['route.plan'].with_user(SUPERUSER_ID).search(domain)
        day_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        for route_plan in route_plans:
            customerList = []
            no =1
            for customer in route_plan.partner_ids:

                customerList.append({
                    'id': customer.partner_id.id,
                    'name': customer.partner_id.name or '',
                    'ref': customer.ref or '',
                    'phone': customer.phone or '',
                    'street': customer.partner_id.street or '',
                    'latitude': customer.latitude or 0.0,
                    'longitude': customer.longitude or 0.0,
                    'sequence': no,
                })
                no += 1
            records.append({
                'id': route_plan.id,
                'name': route_plan.name or '',
                'code': route_plan.code or '',
                'date': route_plan.write_date and route_plan.write_date.strftime(DEFAULT_SERVER_DATETIME_FORMAT) or '',
                'plan_type': route_plan.plan_type or '',
                'based_on': route_plan.based_on or '',
                'begin_partner_id': route_plan.begin_partner_id.id or 0,
                'begin_partner_name': route_plan.begin_partner_id.name or '',
                'begin_partner_lat': route_plan.begin_partner_lat,
                'begin_partner_lng': route_plan.begin_partner_lng,
                'end_partner_id': route_plan.end_partner_id.id or 0,
                'end_partner_name': route_plan.end_partner_id.name or '',
                'end_partner_lat': route_plan.end_partner_lat,
                'end_partner_lng': route_plan.end_partner_lng,
                'partner_count': route_plan.partner_count,
                'customers': customerList,
                'township_ids': [{'id': township.id, 'name': township.name} for township in route_plan.township_ids],
                'channel_ids': [{'id': channel.id, 'name': channel.name} for channel in route_plan.channel_ids],
                'outlet_ids': [{'id': outlet.id, 'name': outlet.name} for outlet in route_plan.outlet_ids],
                'week_id': route_plan.week_id or '',
                'start_date': route_plan.start_date or '',
                'end_date': route_plan.end_date or '',
                'route_plan_date': str(route_plan.route_plan_date) or '',
                'weekday': route_plan.weekday or '',
                'sale_team_id': route_plan.sale_team_id.id or 0,
                'sale_team_name': route_plan.sale_team_id.name or '',
                'write_date': route_plan.write_date.strftime(DEFAULT_SERVER_DATETIME_FORMAT),
            })
        print('///////////', sorted(records, key=lambda d: day_order.index(d["weekday"])))
        return self._response(sorted(records, key=lambda d: day_order.index(d["weekday"])))

    @http.route('/api/get/route_plan', type='json', auth='none', methods=['POST'], csrf=False)
    def _get_route_plan(self, **kwargs):
        records = []
        param = request.jsonrequest
        domain = param.get('domain', '[]')

        if domain:
            try:
                domain = eval(domain)
            except Exception as e:
                return {'success': False, 'message': 'Invalid domain!'}
        write_date_data = param.get('write_date', False)

        if write_date_data:
            date_time_obj = datetime.strptime(write_date_data, '%Y-%m-%d %H:%M:%S')
            write_date = (date_time_obj + relativedelta(seconds=1)).strftime(DEFAULT_SERVER_DATETIME_FORMAT)
            first_time = False
        else:
            first_time = True
        if first_time:
            route_plans = request.env['route.plan'].with_user(SUPERUSER_ID).search(domain)
        else:
            domain = expression.AND([domain, [('write_date', '>', write_date)]])
            route_plans = request.env['route.plan'].with_user(SUPERUSER_ID).search(domain)
        day_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        for route_plan in route_plans:
            customerList = []
            no =1
            for customer in route_plan.partner_ids:

                customerList.append({
                    'id': customer.partner_id.id,
                    'name': customer.partner_id.name or '',
                    'ref': customer.ref or '',
                    'phone': customer.phone or '',
                    'street': customer.partner_id.street or '',
                    'latitude': customer.latitude or 0.0,
                    'longitude': customer.longitude or 0.0,
                    'sequence': no,
                })
                no += 1
            records.append({
                'id': route_plan.id,
                'name': route_plan.name or '',
                'code': route_plan.code or '',
                'date': route_plan.write_date and route_plan.write_date.strftime(DEFAULT_SERVER_DATETIME_FORMAT) or '',
                'plan_type': route_plan.plan_type or '',
                'based_on': route_plan.based_on or '',
                'begin_partner_id': route_plan.begin_partner_id.id or 0,
                'begin_partner_name': route_plan.begin_partner_id.name or '',
                'begin_partner_lat': route_plan.begin_partner_lat,
                'begin_partner_lng': route_plan.begin_partner_lng,
                'end_partner_id': route_plan.end_partner_id.id or 0,
                'end_partner_name': route_plan.end_partner_id.name or '',
                'end_partner_lat': route_plan.end_partner_lat,
                'end_partner_lng': route_plan.end_partner_lng,
                'partner_count': route_plan.partner_count,
                'customers': customerList,
                'township_ids': [{'id': township.id, 'name': township.name} for township in route_plan.township_ids],
                'channel_ids': [{'id': channel.id, 'name': channel.name} for channel in route_plan.channel_ids],
                'outlet_ids': [{'id': outlet.id, 'name': outlet.name} for outlet in route_plan.outlet_ids],
                'week_id': route_plan.week_id or '',
                'weekday': route_plan.weekday or '',
                'sale_team_id': route_plan.sale_team_id.id or 0,
                'sale_team_name': route_plan.sale_team_id.name or '',
                'write_date': route_plan.write_date.strftime(DEFAULT_SERVER_DATETIME_FORMAT),
            })
        return sorted(records, key=lambda d: day_order.index(d["weekday"]))

    @http.route('/stock/on_hand', type='json', auth='none', methods=['POST'], csrf=False)
    def get_product_on_hand_qty(self, **kwargs):
        params = request.jsonrequest
        domain = params.get('domain', '[]')
        company_id = params.get('company_id')
        try:
            domain = eval(domain)
            domain = expression.AND([domain, [('company_id', '=', company_id),('on_hand','=',True)]])
        except Exception as e:
            return {'error': 'Invalid domain!'}
        records = []
        quants = request.env['stock.quant'].with_user(SUPERUSER_ID).search(domain)

        for quant in quants:
            uom = []
            category = []
            product = quant.product_id
            
            if product.categ_id:
                category = [product.categ_id.id, product.categ_id.display_name]
            if product.uom_id:
                uom = [product.uom_id.id, product.uom_id.name]
            if product.image_1920:
                image = product.image_1920.decode('utf-8')
            else:
                image = ''
            customer_taxes = []
            taxes = product.taxes_id
            for tax in taxes:
                customer_taxes.append({
                    'id': tax.id,
                    'name': tax.name,
                    'amount': tax.amount,
                    'price_include': tax.price_include,
                })
            records.append({
                'id': product.id,
                'name': product.name or '',
                'type': product.detailed_type or '',
                'image': image,
                'barcode': product.barcode or '',
                'cost': product.standard_price or 0.0,
                'internal_note': product.description.striptags() if product.description else '',
                'category': category,
                'list_price': product.list_price or 0.0,
                'sale_description': product.description_sale or '',
                'fs_description': product.fs_description or '',
                'internal_ref': product.default_code or '',
                'uom': uom,
                'product_tmpl_id': product.product_tmpl_id.id,
                'on_hand': quant.quantity,
                'multi_uom_qty': convert_to_multi_uom(product, quant.quantity),
                'taxes': customer_taxes,
                'tracking': product.tracking or '',
                'write_date': product.write_date.strftime(DEFAULT_SERVER_DATETIME_FORMAT),
                'location_id': quant.location_id.id,
            })
        return {'success': 1, 'data': records}

    @http.route('/product/multiuom', type='http', auth='none', methods=['GET', 'POST'], csrf=False)
    def get_multi_uom_lines(self, **kwargs):
        values = request.params
        product_group_ids = values.get("product_group_id", False)
        product_group_ids = eval(product_group_ids)
        product_id = values.get('product_id', False)
        product_ids = values.get('product_ids', False)
        if product_id:
            products = request.env['product.product'].with_user(SUPERUSER_ID).browse(eval(product_id))
        elif product_ids:
            products = request.env['product.product'].with_user(SUPERUSER_ID).browse(eval(product_ids))
        else:
            products = request.env['product.product'].with_user(SUPERUSER_ID).search([("product_group_id","in",product_group_ids)])
        query = """
                SELECT      LINE.PRODUCT_TMPL_ID,
                            PP.ID AS PRODUCT_ID,
                            UOM.NAME AS UOM_NAME,
                            LINE.ID,
                            LINE.UOM_ID,
                            LINE.RATIO,
                            LINE.PRICE,
                            LINE.IS_DEFAULT_UOM,
                            TO_CHAR(LINE.WRITE_DATE, 'YYYY-MM-DD HH24:MI:SS') AS WRITE_DATE
                FROM        MULTI_UOM_LINE LINE
                            LEFT JOIN UOM_UOM UOM ON UOM.ID=LINE.UOM_ID
                            LEFT JOIN PRODUCT_TEMPLATE PT ON PT.ID=LINE.PRODUCT_TMPL_ID
                            LEFT JOIN PRODUCT_PRODUCT PP ON PP.PRODUCT_TMPL_ID=PT.ID
                WHERE       LINE.PRODUCT_TMPL_ID IN %s
            """
        request.env.cr.execute(query, (tuple(products.product_tmpl_id.mapped('id')),))
        records = request.env.cr.dictfetchall()
        return self._response({'success': 1, 'data': records})

    @http.route('/sales_team/sales_team', type='json', auth='none', methods=['GET', 'POST'], csrf=False)
    def get_sales_team(self, **kwargs):
        records = []
        values = request.params
        salesTeamCode = values['salesTeamCode']
        teams = request.env['crm.team'].sudo().search([('code', '=', salesTeamCode), ('is_van_team', '=', True)])

        for team in teams:
            records.append({
                'id': team.id,
                'name': team.name or '',
                'code': team.code or '',
                'warehouse_id': team.van_location_id.warehouse_id.id or 0,
                'warehouse_code': team.van_location_id.warehouse_id.code or '',
                'vehicle_id': team.vehicle_id.id or 0,
                'vehicle_name': team.vehicle_id.name or '',
                'van_location_id': team.van_location_id.id or 0,
                'van_location_name': team.van_location_id.complete_name or '',
                'allowed_location_ids': team.allowed_location_ids.ids,
                'product_group_ids': teams.product_group_ids.ids,
                'write_date': team.write_date.strftime(DEFAULT_SERVER_DATETIME_FORMAT),
            })
        if teams:
            return {'success': 1, 'data': records}
        else:
            return {'success': 0}

    @http.route('/van/orders', type='http', auth='none', methods=['GET', 'POST'], csrf=False)
    def get_van_order(self, **kwargs):
        records = []
        domain = kwargs.get('domain', [])
        if domain:
            try:
                domain = eval(domain)
            except Exception as e:
                return {'success': False, 'message': 'Invalid domain!'}
        orders = request.env['van.order'].with_user(SUPERUSER_ID).search(domain)
        for order in orders:
            order_lines = []
            payment_lines = []
            for line in order.order_line_ids:
                order_lines.append({
                    'id': line.id,
                    'description': line.name,
                    'product_id': line.product_id.id,
                    'qty': line.qty,
                    'uom_id': line.uom_id.id,
                    'price_unit': line.price_unit,
                    'tax_ids': [[tax.id, tax.name] for tax in line.tax_ids],
                    'price_total': line.price_total,
                    'price_subtotal': line.price_subtotal,
                })
            for line in order.payment_ids:
                payment_lines.append({
                    'id': line.id,
                    'date': line.date.strftime('%Y-%m-%d %H:%M:%S'),
                    'payment_method_id': line.payment_method_id.id,
                    'amount': line.amount,
                    'currency_id': line.currency_id.id,
                })
            records.append({
                'id': order.id,
                'date': order.date.strftime('%Y-%m-%d %H:%M:%S'),
                'partner_id': order.partner_id.id,
                'warehouse_id': order.warehouse_id.id,
                'location_id': order.location_id.id,
                'fleet_id': order.fleet_id.id,
                'team_id': order.team_id.id,
                'pricelist_id': order.pricelist_id.id,
                'currency_id': order.currency_id.id,
                'amount_untaxed': order.amount_untaxed,
                'amount_tax': order.amount_tax,
                'amount_total': order.amount_total,
                'daily_sale_summary_id': order.daily_sale_summary_id.id,
                'state': order.state,
                'company_id': order.company_id.id,
                'payment_type': order.payment_type,
                'order_lines': order_lines,
                'payment_lines': payment_lines,
                'write_date': order.write_date.strftime(DEFAULT_SERVER_DATETIME_FORMAT),
            })
        return self._response(records)

    @http.route('/api/sale/orders', type='http', auth='none', methods=['GET'], csrf=False)
    def get_sale_orders(self, **kwargs):
        domain = []
        if domain:
            try:
                domain = eval(domain)
            except Exception as e:
                return {'success': False, 'message': 'Invalid domain!'}
        orders = request.env['sale.order'].with_user(SUPERUSER_ID).search(domain)
        records = []
        for order in orders:
            order_lines = []
            for line in order.order_line:
                order_lines.append({
                    'name': line.name,
                    'product_id': line.product_id.id,
                    'product_uom_qty': line.product_uom_qty,
                    'product_uom': line.product_uom.id,
                    'price_unit': line.price_unit,
                })
            records.append({
                'partner_id': order.partner_id.id,
                'partner_invoice_id': order.partner_invoice_id.id,
                'partner_shipping_id': order.partner_shipping_id.id,
                'date_order': order.date_order.strftime('%Y-%m-%d %H:%M:%S') if order.date_order else '',
                'pricelist_id': order.pricelist_id.id,
                'currency_id': order.currency_id.id,
                'payment_term_id': order.payment_term_id.id,
                'warehouse_id': order.warehouse_id.id,
                'user_id': order.user_id.id,
                'team_id': order.team_id.id,
                'order_lines': order_lines,
                'order_id': order.id,
                'write_date': order.write_date.strftime(DEFAULT_SERVER_DATETIME_FORMAT),
            })
        return self._response(records)

    @http.route('/api/qty_stock_request', type='json', auth='none', methods=['GET', 'POST'], csrf=False)
    def qty_stock_request(self, **kwargs):

        records = []
        param = request.jsonrequest
        picking_id = param.get('picking_id')
        user_id = param.get('user_id')
        stock_requisition = request.env['stock.picking'].with_user(SUPERUSER_ID).search([('id', '=', picking_id)])
        records = []
        for stockRequest in stock_requisition:
            productList = []

            for product in stockRequest.move_lines:
                if product.multi_quantity_done > 0:
                    productList.append({
                        'id': product.id,
                        'completeName': product.name,
                        'product_id': product.product_id.id,
                        'product_name': product.product_id.name,
                        'uom_id': product.product_uom.id,
                        'uom_name': product.product_uom.name,
                        'multi_uom_line_id': product.multi_uom_line_id.id or 0,
                        'multi_uom_line_name': product.multi_uom_line_id.uom_id.name or '',
                        'lot_id': product.lot_ids and product.lot_ids[0].id or 0,
                        'lot_name': product.lot_ids and product.lot_ids[0].name or '',
                        'qty': product.multi_uom_qty,
                        'done_qty': product.multi_quantity_done,
                    })

            records.append({
                'id': stockRequest.id,
                'name': stockRequest.name,
                'date': str(stockRequest.scheduled_date),
                'request_by': stockRequest.user_id.name or '',
                'scheduled_date': str(stockRequest.scheduled_date) or '',
                'location_id': stockRequest.location_id.id or 0,
                'location_dest_id': stockRequest.location_dest_id.id or 0,
                'state': stockRequest.state,
                'user_id': stockRequest.user_id.id,
                'approve_person_name': stockRequest.approve_user_id.name or '',
                'team_id': stockRequest.team_id.id,
                'team_name': stockRequest.team_id.name or '',
                'products': productList,
                'mobileSRRef': stockRequest.origin or '',
                'write_date': stockRequest.write_date.strftime(DEFAULT_SERVER_DATETIME_FORMAT),
            })
        stock_requisition.update({
            'received_user_id': user_id
        })
        return records

    @http.route('/stock_request/stock_request', type='http', auth='none', methods=['GET', 'POST'], csrf=False)
    def get_stock_request(self, **kwargs):
        records = []
        param = request.params
        domain = param.get('domain', '[]')
        if domain:
            try:
                domain = eval(domain)
            except Exception as e:
                return {'success': False, 'message': 'Invalid domain!'}
        write_date_data = param.get('write_date', False)

        if write_date_data:
            date_time_obj = datetime.strptime(write_date_data, '%Y-%m-%d %H:%M:%S')
            write_date = (date_time_obj + relativedelta(seconds=1)).strftime(DEFAULT_SERVER_DATETIME_FORMAT)
            first_time = False
        else:
            first_time = True
        if first_time:
            stock_requisition = request.env['stock.picking'].with_user(SUPERUSER_ID).search(domain)
        else:
            domain = expression.AND([domain, [('write_date', '>=', write_date)]])
            stock_requisition = request.env['stock.picking'].with_user(SUPERUSER_ID).search(domain)

        for stockRequest in stock_requisition:
            productList = []

            for product in stockRequest.move_lines:
                productList.append({
                    'id': product.id,
                    'completeName': product.name,
                    'product_id': product.product_id.id,
                    'product_name': product.product_id.name,
                    'uom_id': product.product_uom.id,
                    'uom_name': product.product_uom.name,
                    'multi_uom_line_id': product.multi_uom_line_id.id or 0,
                    'multi_uom_line_name': product.multi_uom_line_id.uom_id.name or '',
                    'lot_id': product.lot_ids and product.lot_ids[0].id or 0,
                    'lot_name': product.lot_ids and product.lot_ids[0].name or '',
                    'qty': product.multi_uom_qty,
                    'done_qty': product.multi_quantity_done,
                })

            records.append({
                'id': stockRequest.id,
                'name': stockRequest.name,
                'date': str(stockRequest.scheduled_date),
                'request_by': stockRequest.user_id.name or '',
                'scheduled_date': str(stockRequest.scheduled_date) or '',
                'location_id': stockRequest.location_id.id or 0,
                'location_dest_id': stockRequest.location_dest_id.id or 0,
                'state': stockRequest.state,
                'user_id': stockRequest.user_id.id,
                'approve_person_name': stockRequest.approve_user_id.name or '',
                'team_id': stockRequest.team_id.id,
                'team_name': stockRequest.team_id.name or '',
                'products': productList,
                'mobileSRRef': stockRequest.origin or '',
                'write_date': stockRequest.write_date.strftime(DEFAULT_SERVER_DATETIME_FORMAT),
            })
        return self._response(records)

    @http.route('/api/get/stock_return', type='json', auth='none', methods=['POST'], csrf=False)
    def get_stock_return(self, **kwargs):
        records = []
        params = request.jsonrequest
        uid = request.session.uid
        domain = params.get('domain', '[]')
        if not uid:
            return {'success': False, 'error': 'Invalid cookie.'}
        try:
            domain = eval(domain)
        except Exception as e:
            return {'error': 'Invalid domain.'}
        write_date_data = params.get('write_date', False)

        if write_date_data:
            date_time_obj = datetime.strptime(write_date_data, '%Y-%m-%d %H:%M:%S')
            write_date = (date_time_obj + relativedelta(seconds=1)).strftime(DEFAULT_SERVER_DATETIME_FORMAT)
            first_time = False
        else:
            first_time = True
        if first_time:
            stock_returns = request.env['stock.picking'].with_user(SUPERUSER_ID).search(domain)
        else:
            domain = expression.AND([domain, [('write_date', '>=', params.get('write_date'))]])
            stock_returns = request.env['stock.picking'].with_user(SUPERUSER_ID).search(domain)

        for stockReturn in stock_returns:
            productList = []
            for product in stockReturn.move_lines:
                productList.append({
                    'id': product.id,
                    'completeName': product.name,
                    'product_id': product.product_id.id,
                    'product_name': product.product_id.name,
                    'uom_id': product.product_uom.id,
                    'uom_name': product.product_uom.name,
                    'multi_uom_line_id': product.multi_uom_line_id.id or 0,
                    'multi_uom_line_name': product.multi_uom_line_id.uom_id.name or '',
                    'lot_id': product.lot_ids and product.lot_ids[0].id or 0,
                    'lot_name': product.lot_ids and product.lot_ids[0].name or '',
                    'qty': product.multi_uom_qty,
                    'done_qty': product.multi_quantity_done,
                })
            records.append({
                'id': stockReturn.id,
                'name': stockReturn.name,
                'date': str(stockReturn.scheduled_date),
                'request_by': stockReturn.user_id.name or '',
                'scheduled_date': str(stockReturn.scheduled_date) or '',
                'location_id': stockReturn.location_id.id or 0,
                'location_dest_id': stockReturn.location_dest_id.id or 0,
                'state': stockReturn.state,
                'user_id': stockReturn.user_id.id,
                'team_id': stockReturn.team_id.id,
                'team_name': stockReturn.team_id.name,
                'products': productList,
                'mobileSRRef': stockReturn.origin or '',
                'write_date': stockReturn.write_date.strftime(DEFAULT_SERVER_DATETIME_FORMAT),
            })

        return records

    @http.route('/api/get/stock_validation', type='json', auth='none', methods=['GET', 'POST'], csrf=False)
    def get_stock_validation(self, **kwargs):
        records = []
        param = request.jsonrequest
        sale_team_id = param.get('sale_team_id')
        company_id = param.get('company_id')
        domain = param.get('domain', '[]')
        if domain:
            try:
                domain = eval(domain)
            except Exception as e:
                return {'success': False, 'message': 'Invalid domain!'}
        stock_return_validation = request.env['stock.picking'].with_user(SUPERUSER_ID).search([('is_fs_return','=',True), ('state', '!=', 'done'), ('state', '!=', 'cancel'),('team_id','=',sale_team_id),('company_id','=',company_id)])
        stock_scrap_validation = request.env['stock.multi.scrap'].with_user(SUPERUSER_ID).search([('is_van_scrap','=',True), ('state', '!=', 'done'), ('state', '!=', 'cancel'),('team_id','=',sale_team_id),('company_id','=',company_id)])
        # daily_sale_validation = request.env['daily.sale.summary'].with_user(SUPERUSER_ID).search([('state','!=','posted'),('team_id','=',sale_team_id),('company_id','=',company_id)])
        if not stock_scrap_validation and not stock_return_validation:
            return {'success': True, 'message': 'All stocks are validated'}
        if stock_return_validation or stock_scrap_validation or daily_sale_validation:
            return {'success': False, 'message': 'Some stocks are not validated.'}

    @http.route('/sale/payment/method', type='http', auth='none', methods=['GET', 'POST'], csrf=False)
    def get_payment_methods(self, **kwargs):
        params = request.params
        uid = request.session.uid
        domain = params.get('domain', '[]')
        if not uid:
            return self._response({'success': False, 'error': 'Invalid cookie.'}, status_code=400)
        try:
            domain = eval(domain)
        except Exception as e:
            return self._response({'error': 'Invalid domain.'}, status_code=400)
        payment_methods = request.env['fieldsale.payment.method'].with_user(SUPERUSER_ID).search(domain)
        records = []
        for payment_method in payment_methods:
            records.append({
                'id': payment_method.id,
                'payment_type': payment_method.journal_id.type,
                'name': payment_method.name,
                'write_date': payment_method.write_date.strftime(DEFAULT_SERVER_DATETIME_FORMAT),
            })
        return self._response(records)

    @http.route('/sale/payment/term', type='http', auth='none', methods=['GET', 'POST'], csrf=False)
    def get_payment_terms(self, **kwargs):
        params = request.params
        uid = request.session.uid
        domain = params.get('domain', '[]')
        if not uid:
            return self._response({'success': False, 'error': 'Invalid cookie.'}, status_code=400)
        try:
            domain = eval(domain)
        except Exception as e:
            return self._response({'error': 'Invalid domain.'}, status_code=400)
        payment_terms = request.env['account.payment.term'].with_user(SUPERUSER_ID).search(domain)
        records = []
        for payment_term in payment_terms:
            records.append({
                'id': payment_term.id,
                'name': payment_term.name,
                'write_date': payment_term.write_date.strftime(DEFAULT_SERVER_DATETIME_FORMAT),
            })
        return self._response(records)

    @http.route('/contact/township', type='http', auth='none', methods=['GET', 'POST'], csrf=False)
    def get_townships(self, **kwargs):
        params = request.params
        uid = request.session.uid
        domain = params.get('domain', '[]')
        if not uid:
            return self._response({'success': False, 'error': 'Invalid cookie.'}, status_code=400)
        try:
            domain = eval(domain)
        except Exception as e:
            return self._response({'error': 'Invalid domain.'}, status_code=400)
        townships = request.env['res.township'].with_user(SUPERUSER_ID).search(domain)
        records = []
        for township in townships:
            records.append({
                'id': township.id,
                'name': township.name,
                'code': township.code,
                'zip': township.zip,
                'city_id': township.city_id and township.city_id.id or 0,
                'city_name': township.city_id.name or '',
                'state_id': township.city_id.state_id and township.city_id.state_id.id or 0,
                'state_name': township.city_id.state_id.name or '',
                'write_date': township.write_date.strftime(DEFAULT_SERVER_DATETIME_FORMAT),
            })
        return self._response(records)

    @http.route('/contact/city', type='http', auth='none', methods=['GET', 'POST'], csrf=False)
    def get_cities(self, **kwargs):
        params = request.params
        uid = request.session.uid
        domain = params.get('domain', '[]')
        if not uid:
            return self._response({'success': False, 'error': 'Invalid cookie.'}, status_code=400)
        try:
            domain = eval(domain)
        except Exception as e:
            return self._response({'error': 'Invalid domain.'}, status_code=400)
        cities = request.env['res.city'].with_user(SUPERUSER_ID).search(domain)
        records = []
        for city in cities:
            records.append({
                'id': city.id or '',
                'name': city.name or '',
                'code': city.code or '',
                'state_id': city.state_id.id or 0,
                'state_name': city.state_id.name or '',
                'country_id': city.country_id.id or 0,
                'country_name': city.country_id.name or '',
                'write_date': city.write_date.strftime(DEFAULT_SERVER_DATETIME_FORMAT) or '',
            })
        return self._response(records)

    @http.route('/contact/state', type='http', auth='none', methods=['GET', 'POST'], csrf=False)
    def get_states(self, **kwargs):
        params = request.params
        uid = request.session.uid
        domain = params.get('domain', '[]')
        if not uid:
            return self._response({'success': False, 'error': 'Invalid cookie.'}, status_code=400)
        try:
            domain = eval(domain)
        except Exception as e:
            return self._response({'error': 'Invalid domain.'}, status_code=400)
        states = request.env['res.country.state'].with_user(SUPERUSER_ID).search(domain)
        records = []
        for state in states:
            records.append({
                'id': state.id,
                'name': state.name,
                'code': state.code,
                'country_id': state.country_id.id,
                'country_name': state.country_id.name,
                'write_date': state.write_date.strftime(DEFAULT_SERVER_DATETIME_FORMAT),
            })
        return self._response(records)

    @http.route('/sale/channel', type='http', auth='none', methods=['GET', 'POST'], csrf=False)
    def get_sale_channels(self, **kwargs):
        params = request.params
        uid = request.session.uid
        domain = params.get('domain', '[]')
        if not uid:
            return self._response({'success': False, 'error': 'Invalid cookie.'}, status_code=400)
        try:
            domain = eval(domain)
        except Exception as e:
            return self._response({'error': 'Invalid domain.'}, status_code=400)
        sale_channels = request.env['res.sale.channel'].with_user(SUPERUSER_ID).search(domain)
        records = []
        for sale_channel in sale_channels:
            records.append({
                'id': sale_channel.id,
                'name': sale_channel.name,
                'write_date': sale_channel.write_date.strftime(DEFAULT_SERVER_DATETIME_FORMAT),
            })
        return self._response(records)

    @http.route('/contact/outlet', type='http', auth='none', methods=['GET', 'POST'], csrf=False)
    def get_outlet_types(self, **kwargs):
        params = request.params
        uid = request.session.uid
        domain = params.get('domain', '[]')
        if not uid:
            return self._response({'success': False, 'error': 'Invalid cookie.'}, status_code=400)
        try:
            domain = eval(domain)
        except Exception as e:
            return self._response({'error': 'Invalid domain.'}, status_code=400)
        outlet_types = request.env['res.partner.outlet'].with_user(SUPERUSER_ID).search(domain)
        records = []
        for outlet_type in outlet_types:
            records.append({
                'id': outlet_type.id,
                'name': outlet_type.name,
                'sale_channel_id': outlet_type.channel_id.id,
                'sale_channel_name': outlet_type.channel_id.name,
                'write_date': outlet_type.write_date.strftime(DEFAULT_SERVER_DATETIME_FORMAT),
            })
        return self._response(records)

    @http.route('/visitreport/reasontype', type='http', auth='none', methods=['GET', 'POST'], csrf=False)
    def get_visit_report_reason_types(self, **kwargs):
        params = request.params
        uid = request.session.uid
        domain = params.get('domain', '[]')
        if not uid:
            return self._response({'success': False, 'error': 'Invalid cookie.'}, status_code=400)
        try:
            domain = eval(domain)
        except Exception as e:
            return self._response({'error': 'Invalid domain.'}, status_code=400)
        reason_types = request.env['visit.report.reason.type'].with_user(SUPERUSER_ID).search(domain)
        records = []
        for reason_type in reason_types:
            records.append({
                'id': reason_type.id,
                'name': reason_type.name,
                'write_date': reason_type.write_date.strftime(DEFAULT_SERVER_DATETIME_FORMAT),
            })
        return self._response(records)

    @http.route('/product/pricelist', type='http', auth='none', methods=['GET', 'POST'], csrf=False)
    def get_sale_price_lists(self, **kwargs):
        params = request.params
        uid = request.session.uid
        domain = params.get('domain', '[]')
        if not uid:
            return self._response({'success': False, 'error': 'Invalid cookie.'}, status_code=400)
        try:
            domain = eval(domain)
        except Exception as e:
            return self._response({'error': 'Invalid domain.'}, status_code=400)
        price_lists = request.env['product.pricelist'].with_user(SUPERUSER_ID).search(domain)
        mode = request.env['ir.config_parameter'].with_user(SUPERUSER_ID).get_param('product.product_pricelist_setting')
        records = []
        for price_list in price_lists:
            items = []
            if mode == 'uom':
                for item in price_list.pricelist_item_uom_ids:
                    items.append({
                        'product_id': item.product_id.id,
                        'multi_uom_line_id': item.multi_uom_line_id.id,
                        'qty': item.pricelist_qty,
                        'price': item.price,
                    })
            else:
                for item in price_list.item_ids:
                    items.append({
                        'total_price': item.total_price,
                        'compute_price': item.compute_price or '',
                        'applied_on': item.applied_on or '',
                        'category_id': item.categ_id.id or 0,
                        'product_tmpl_id': item.product_tmpl_id.id or 0,
                        'product_id': item.product_id.id or 0,
                        'min_quantity': item.min_quantity,
                        'date_start': item.date_start and item.date_start.strftime(DEFAULT_SERVER_DATE_FORMAT) or '',
                        'date_end': item.date_end and item.date_end.strftime(DEFAULT_SERVER_DATE_FORMAT) or '',
                        'fixed_price': item.fixed_price,
                        'percent_price': item.percent_price,
                        'base': item.base or 0,
                        'price_discount': item.price_discount,
                        'price_surcharge': item.price_surcharge,
                        'price_round': item.price_round,
                        'price_min_margin': item.price_min_margin,
                        'price_max_margin': item.price_max_margin,
                        'base_pricelist_id': item.base_pricelist_id.id or 0,
                        'multi_uom_line_id': item.multi_uom_line_id.id,
                        'multi_uom_line_name': item.multi_uom_line_id.uom_id.name,
                    })
            records.append({
                'id': price_list.id,
                'name': price_list.name_get()[0][1],
                'currency_id': price_list.currency_id.id,
                'currency_name': price_list.currency_id.name,
                'company_id': price_list.company_id.id or 0,
                'country_group_ids': price_list.country_group_ids.ids,
                'price_list_items': items,
                'setting': request.env['ir.config_parameter'].with_user(SUPERUSER_ID).get_param(
                    'product.product_pricelist_setting'),
                'write_date': price_list.write_date.strftime(DEFAULT_SERVER_DATETIME_FORMAT),
            })
        return self._response(records)

    @http.route('/sale/product/price', type='json', auth='none', methods=['POST'], csrf=False)
    def get_product_price(self):
        params = request.jsonrequest
        uid = request.session.uid
        try:
            product_id = params['product_id']
            partner_id = params['partner_id']
            uom_id = params['uom_id']
            qty = params['qty']
            date = params['date']
            price_list_id = params['price_list_id']
        except KeyError as e:
            return {'error': 'Please make sure to give all parameters.'}
        partner_id = request.env['res.partner'].with_user(SUPERUSER_ID).browse(partner_id)
        uom_id = request.env['uom.uom'].with_user(SUPERUSER_ID).browse(uom_id)
        price_list_id = request.env['product.pricelist'].with_user(SUPERUSER_ID).browse(price_list_id)
        product = request.env['product.product'].with_context(
            lang=partner_id.lang,
            partner=partner_id.id,
            quantity=qty,
            date=date,
            pricelist=price_list_id.id,
            uom=uom_id.id,
        ).with_user(SUPERUSER_ID).browse(product_id)
        return {'price': product.price}

    @http.route('/accounting/tax', type='http', auth='none', methods=['GET', 'POST'], csrf=False)
    def get_taxes(self, **kwargs):
        params = request.params
        uid = request.session.uid
        domain = params.get('domain', '[]')
        if not uid:
            return self._response({'success': False, 'error': 'Invalid cookie.'}, status_code=400)
        try:
            domain = eval(domain)
        except Exception as e:
            return self._response({'error': 'Invalid domain.'}, status_code=400)
        taxes = request.env['account.tax'].with_user(SUPERUSER_ID).search(domain)
        records = []
        for tax in taxes:
            records.append({
                'id': tax.id,
                'name': tax.name,
                'amount': tax.amount,
                'price_include': tax.price_include,
                'write_date': tax.write_date.strftime(DEFAULT_SERVER_DATETIME_FORMAT),
            })
        return self._response(records)

    @http.route('/api/get/stock-scrap', type='json', auth='none', methods=['POST'], csrf=False)
    def get_stock_scraps(self, **kwargs):
        params = request.jsonrequest
        uid = request.session.uid
        domain = params.get('domain', '[]')
        additional_fields = params.get('additional_fields', [])
        if not uid:
            return {'success': False, 'error': 'Invalid cookie.'}
        try:
            domain = eval(domain)
        except Exception as e:
            return {'error': 'Invalid domain.'}
        scraps = request.env['stock.multi.scrap'].with_user(SUPERUSER_ID).search(domain)
        records = []
        for scrap in scraps:
            vals = {
                'id': scrap.id,
                'state': scrap.state,
                'write_date': scrap.write_date.strftime(DEFAULT_SERVER_DATETIME_FORMAT),
            }
            for additional_field in additional_fields:
                vals[additional_field] = getattr(scrap, additional_field)
            records.append(vals)
        return records

    @http.route('/api/get/currency', type='json', auth='none', methods=['POST'], csrf=False)
    def get_currencies(self, **kwargs):
        params = request.jsonrequest
        uid = request.session.uid
        domain = params.get('domain', '[]')
        additional_fields = params.get('additional_fields', [])
        if not uid:
            return {'success': False, 'error': 'Invalid cookie.'}
        try:
            domain = eval(domain)
        except Exception as e:
            return {'error': 'Invalid domain.'}
        first_time = params.get('first_time', False)
        if first_time:
            currencies = request.env['res.currency'].sudo().with_company(params['company_id']).search(domain)
        else:
            domain = expression.AND([domain, [('write_date', '>=', params['write_date'])]])
            currencies = request.env['res.currency'].sudo().with_company(params['company_id']).search(domain)
        records = []
        for currency in currencies:
            vals = {
                'id': currency.id,
                'name': currency.name,
                'symbol': currency.symbol,
                'currency_unit_label': currency.currency_unit_label or '',
                'write_date': currency.write_date.strftime(DEFAULT_SERVER_DATETIME_FORMAT),
            }
            for additional_field in additional_fields:
                vals[additional_field] = getattr(currency, additional_field)
            rates = []
            for rate in currency.rate_ids:
                rate_vals = {
                    'id': rate.id,
                    'date': rate.name,
                    'rate': rate.inverse_company_rate,
                }
                rates.append(rate_vals)
            vals['rates'] = rates
            records.append(vals)
        return records

    @http.route('/api/get/payment-collection-one', type='json', auth='none', methods=['POST'], csrf=False)
    def get_payment_collections_one(self, **kwargs):
        params = request.jsonrequest
        uid = request.session.uid
        domain = params.get('domain', '[]')
        if not uid:
            return {'success': False, 'error': 'Invalid cookie.'}
        try:
            domain = eval(domain)
        except Exception as e:
            return {'error': 'Invalid domain.'}
        payment_collections = request.env['payment.collection.one'].with_user(SUPERUSER_ID).search(domain)
        company = request.env['res.users'].sudo().browse(uid).company_id
        records = []
        for payment_collection in payment_collections:
            
            records.append({
                'id': payment_collection.id,
                'name': payment_collection.name,
                'assigned_person_name': payment_collection.create_uid.name,
                'partner_id': payment_collection.partner_id.id,
                'partner_name': payment_collection.partner_id.name,
                'partner_ref': payment_collection.partner_id.ref,
                'invoice_address_id': payment_collection.invoice_address_id.id,
                'invoice_address_name': payment_collection.invoice_address_id.name,
                'invoice_address': payment_collection.invoice_address,
                'sale_man_id': payment_collection.sale_man_id.id,
                'sale_man_name': payment_collection.sale_man_id.name,
                'team_id': payment_collection.team_id.id,
                'team_name': payment_collection.team_id.name,
                'date': str(payment_collection.date),
                'state': payment_collection.state,
                'to_collect_date': str(payment_collection.to_collect_date),
                'to_collect_amt': payment_collection.to_collect_amt,
                'collected_amt': payment_collection.collected_amt,
                'company_id': payment_collection.company_id.id,
                'company_name': payment_collection.company_id.name,
            })
            
        return {'success': True, 'records': records}

    @http.route('/api/get/payment-collection', type='json', auth='none', methods=['POST'], csrf=False)
    def get_payment_collections(self, **kwargs):
        params = request.jsonrequest
        uid = request.session.uid
        domain = params.get('domain', '[]')
        if not uid:
            return {'success': False, 'error': 'Invalid cookie.'}
        try:
            domain = eval(domain)
        except Exception as e:
            return {'error': 'Invalid domain.'}
        payment_collections = request.env['payment.collection'].with_user(SUPERUSER_ID).search(domain)
        company = request.env['res.users'].sudo().browse(uid).company_id
        records = []
        for payment_collection in payment_collections:
            invoices = []
            payments = []
            address = ''
            total_amt = 0
            invoice_addresses = payment_collection.partner_id.child_ids.filtered(lambda p: p.type == 'invoice')
            if invoice_addresses:
                partner = invoice_addresses[-1]
            else:
                partner = payment_collection.partner_id
            street = partner.street or ''
            street2 = partner.street2 or ''
            township = partner.township_id.name or ''
            city = partner.x_city_id.name or ''
            region = partner.state_id.name or ''
            if street:
                address += street + ', '
            if street2:
                address += street2 + ', '
            if township:
                address += township + ', '
            if city:
                address += city + ', '
            if region:
                address += region
            for invoice in payment_collection.line_ids:
                if invoice.payment_state != "received":
                    sale_order = invoice.invoice_id.line_ids.sale_line_ids.order_id
                    if sale_order:
                        order = sale_order[-1].name
                    else:
                        order = ''
                    total_amt += invoice.invoice_id.currency_id._convert(invoice.amount_residual,
                                                                         company.currency_id,
                                                                         company,
                                                                         invoice.invoice_date)
                    invoices.append({
                        'id': invoice.id,
                        'invoice_id': invoice.invoice_id.id,
                        'invoice_number': invoice.invoice_id.name,
                        'invoice_date': invoice.invoice_date and invoice.invoice_date.strftime(
                            DEFAULT_SERVER_DATE_FORMAT) or '',
                        'due_date': invoice.due_date and invoice.due_date.strftime('%d/%m/%Y') or '',
                        'amount_total': invoice.amount_total,
                        'amount_paid': 0.0,
                        'amount_residual': invoice.amount_residual,
                        'amount_last_paid': invoice.amount_last_paid,
                        'last_payment_date': invoice.last_payment_date and invoice.last_payment_date.strftime(
                            DEFAULT_SERVER_DATE_FORMAT) or '',
                        'currency_id': invoice.currency_id.id,
                        'currency_name': invoice.currency_id.name,
                        'payment_state': invoice.payment_state or '',
                        'order': order,
                    })
            for payment in payment_collection.payment_ids:
                payments.append({
                    'id': payment.id,
                    'date': payment.date.strftime(DEFAULT_SERVER_DATE_FORMAT),
                    'payment_method_id': payment.payment_method_id.id,
                    'payment_method_name': payment.payment_method_id.name,
                    'amount': payment.amount,
                    'currency_id': payment.currency_id.id,
                    'currency_name': payment.currency_id.name,
                })
            if payment_collection.invoice_address_id:
                partner_name = str(payment_collection.invoice_address_id.name) + "_ " + str(payment_collection.partner_id.name) 
            else:
                partner_name = str(payment_collection.partner_id.name)
            records.append({
                'id': payment_collection.id,
                'name': payment_collection.name,
                'assigned_person_name': payment_collection.create_uid.name,
                'partner_id': payment_collection.partner_id.id,
                'partner_name': partner_name,
                'partner_ref': payment_collection.partner_id.ref,
                'sale_man_id': payment_collection.sale_man_id.id,
                'sale_man_name': payment_collection.sale_man_id.name,
                'invoice_address_id': payment_collection.invoice_address_id.id,
                'team_id': payment_collection.team_id.id,
                'team_name': payment_collection.team_id.name,
                'date': payment_collection.date.strftime(DEFAULT_SERVER_DATETIME_FORMAT),
                'to_collect_date': payment_collection.to_collect_date.strftime(DEFAULT_SERVER_DATE_FORMAT),
                'company_id': payment_collection.company_id.id,
                'company_name': payment_collection.company_id.name,
                'state': payment_collection.state,
                'address': address,
                'total_amt': total_amt,
                'signature': payment_collection.signature or '',
                'signed_by': payment_collection.signed_by or '',
                'signed_on': payment_collection.signed_on and payment_collection.signed_on.strftime(
                    DEFAULT_SERVER_DATETIME_FORMAT) or '',
                'invoices': invoices,
                'payments': payments,
                'write_date': payment_collection.write_date.strftime(DEFAULT_SERVER_DATETIME_FORMAT),
            })
        return records

    @http.route('/api/get/invoice', type='json', auth='none', methods=['POST'], csrf=False)
    def get_invoices(self, **kwargs):

        params = request.jsonrequest
        uid = request.session.uid
        domain = params.get('domain', str([('move_type', '=', 'out_invoice'),
                                           ('state', '=', 'posted'),
                                           ('payment_state', 'in', ['not_paid', 'partial'])]))
        today_payment_only = params.get('today_payment_only')
        delivery_invoice = params.get('delivery_invoice')
        if not uid:
            return {'success': False, 'error': 'Invalid cookie.'}
        try:
            domain = eval(domain)
        except Exception as e:
            return {'error': 'Invalid domain.'}
        invoices = request.env['account.move'].with_user(SUPERUSER_ID).search(domain, order='write_date desc')
        records = []

        for invoice in invoices:

            payments = request.env['account.payment'].with_user(SUPERUSER_ID).search([]).filtered(
                lambda payment: invoice.id in payment.reconciled_invoice_ids.ids)
            if today_payment_only:
                payments = payments.filtered(lambda payment: payment.date == fields.Date.today())
            invoice_payments = []
            for payment in payments:

                if delivery_invoice:
                    invoice_payments.append({

                        'payment_id': payment.id,
                        'payment_name': payment.name or '',
                        'payment_date': payment.date,
                        'payment_amount': payment.amount,
                    })


            records.append({
                'id': invoice.id,
                'name': invoice.name or '',
                'partner_id': invoice.partner_id.id or 0,
                'partner_name': invoice.partner_id.name or '',
                'invoice_date': invoice.invoice_date and invoice.invoice_date.strftime(
                    DEFAULT_SERVER_DATE_FORMAT) or '',
                'due_date': invoice.invoice_date_due and invoice.invoice_date_due.strftime('%d/%m/%Y') or '',
                'amount_total': invoice.amount_total,
                'amount_residual': invoice.amount_residual,
                'currency_id': invoice.currency_id.id or 0,
                'currency_name': invoice.currency_id.name or '',
                'payment_state': invoice.payment_state or '',
                'write_date': invoice.write_date.strftime(DEFAULT_SERVER_DATETIME_FORMAT),
                'payments': invoice_payments,
            })

        return records

    @http.route('/api/get/stock-transfer', type='json', auth='none', methods=['POST'], csrf=False)
    def get_stock_transfers(self, **kwargs):
        records = []
        params = request.jsonrequest
        uid = request.session.uid
        user = request.env['res.users'].sudo().browse(uid)
        domain = params.get('domain', '[]')
        if not uid:
            return {'success': False, 'error': 'Invalid cookie.'}
        try:
            domain = eval(domain)
        except Exception as e:
            return {'error': 'Invalid domain.'}
        pickings = request.env['stock.picking'].with_user(SUPERUSER_ID).search(domain)
        for picking in pickings:
            lines = []
            for line in picking.move_lines:
                lines.append({
                    'id': line.id,
                    'completeName': line.name or '',
                    'product_id': line.product_id and line.product_id.id or 0,
                    'product_name': line.product_id.name or '',
                    'uom_id': line.multi_uom_line_id and line.multi_uom_line_id.id or 0,
                    'uom_name': line.multi_uom_line_id.uom_id.name or '',
                    'lot_id': line.lot_id.id or 0,
                    'lot_name': line.lot_id.name or '',
                    'multi_uom_line_id': line.multi_uom_line_id.id or 0,
                    'multi_uom_line_name': line.multi_uom_line_id.uom_id.name or '',
                    'qty': line.multi_uom_qty,

                })
            records.append({
                'id': picking.id,
                'name': picking.name or '',
                'date': picking.scheduled_date and picking.scheduled_date.strftime(
                    DEFAULT_SERVER_DATETIME_FORMAT) or '',
                'location_id': picking.location_id.id or 0,
                'location_dest_id': picking.location_dest_id.id or 0,
                'state': picking.state,
                'sender_id': picking.sender_id.id or 0,
                'sender_name': picking.sender_id.name or '',
                'receiver_id': picking.receiver_id.id or 0,
                'receiver_name': picking.receiver_id.name or '',
                'sender_fleet_id': picking.sender_fleet_id.id or 0,
                'sender_fleet_name': picking.sender_fleet_id.id or '',
                'receiver_fleet_id': picking.receiver_fleet_id.id or 0,
                'receiver_fleet_name': picking.receiver_fleet_id.id or '',
                'origin': picking.origin or '',
                'company_id': picking.company_id.id or 0,
                'company_name': picking.company_id.name or '',
                'products': lines,
                'write_date': picking.write_date.strftime(DEFAULT_SERVER_DATETIME_FORMAT),
            })
        return records

    @http.route('/api/get/promotion-program', type='json', auth='none', methods=['POST'], csrf=False)
    def get_promotion_programs(self, **kwargs):

        records = []
        params = request.jsonrequest
        uid = request.session.uid
        domain = params.get('domain', '[]')
        if not uid:
            return {'success': False, 'error': 'Invalid cookie.'}
        try:
            domain = eval(domain)
        except Exception as e:
            return {'error': 'Invalid domain.'}
        programs = request.env['promotion.program'].sudo().search(domain)
        for program in programs:
            if program.active == True:
                lines = []
                if program.type == 'buy_x_get_y':
                    for line in program.buy_x_get_y_line_ids:
                        lines.append({
                            'product_x_id': line.product_x_id.id or 0,
                            'product_x_name': line.product_x_id.name or '',
                            'product_x_qty': line.product_x_qty,
                            'operator': line.operator or '',
                            'product_y_id': line.product_y_id.id or 0,
                            'product_y_name': line.product_y_id.name or '',
                            'product_y_qty': line.product_y_qty,
                            'promotion_account_id': line.promotion_account_id.id or 0,
                            'promotion_account_name': line.promotion_account_id.name or '',
                        })
                elif program.type == 'disc_on_qty':
                    for line in program.disc_on_qty_line_ids:
                        lines.append({
                            'product_id': line.product_id.id or 0,
                            'product_name': line.product_id.name or '',
                            'operator': line.operator or '',
                            'qty': line.qty,
                            'discount_type': line.discount_type or '',
                            'discount_amt': line.discount_amt,
                            'promotion_product_id': line.promotion_product_id.id or 0,
                            'promotion_product_name': line.promotion_product_id.name or '',
                        })
                elif program.type == 'disc_comb_prods':
                    for line in program.disc_on_combination_line_ids:
                        lines.append({
                            'product_ids': [{'id': product.id, 'name': product.name} for product in line.product_ids],
                            'discount_type': line.discount_type or '',
                            'discount_amt': line.discount_amt,
                            'promotion_product_id': line.promotion_product_id.id or 0,
                            'promotion_product_name': line.promotion_product_id.name or '',
                        })
                elif program.type == 'disc_comb_prods_qty':
                    for line in program.disc_on_combination_qty_line_ids:
                        lines.append({
                            'product_id': line.product_id.id or 0,
                            'product_name': line.product_id.name or 0,
                            'min_qty': line.min_qty,
                            'discount_type': line.discount_type or '',
                            'discount': line.discount,
                            'promotion_product_id': line.promotion_product_id.id or 0,
                            'promotion_product_name': line.promotion_product_id.name or '',
                        })
                elif program.type == 'promo_based_price_segment_combi':
                    for line in program.disc_on_price_and_combination_line_ids:
                        lines.append({
                            'product_ids': [{'id': product.id, 'name': product.name} for product in line.product_ids],
                            'price_range_from': line.price_range_from,
                            'price_range_to': line.price_range_to,
                            'reward_type': line.reward_type or '',
                            'discount': line.discount,
                            'promotion_product_id': line.promotion_product_id.id or 0,
                            'promotion_product_name': line.promotion_product_id.name or '',
                            'account_id': line.account_id.id or 0,
                            'account_name': line.account_id.name or '',
                        })
                elif program.type == 'promo_based_price_segment_multi':
                    for line in program.disc_on_price_range_multi_line_ids:
                        lines.append({
                            'product_id': line.product_id.id or 0,
                            'product_name': line.product_id.name or '',
                            'category_id': line.category_id.id or 0,
                            'category_name': line.category_id.name or '',
                            'price_range_from': line.price_range_from,
                            'price_range_to': line.price_range_to,
                            'reward_type': line.reward_type or '',
                            'discount': line.discount,
                            'promotion_product_id': line.promotion_product_id.id or 0,
                            'promotion_product_name': line.promotion_product_id.name or '',
                            'account_id': line.account_id.id or 0,
                            'account_name': line.account_id.name or '',
                        })

            records.append({
                'id': program.id,
                'name': program.name or '',
                'type': program.type or '',
                'promo_code': program.promo_code or '',
                'use_promo_code': program.use_promo_code,
                'start_date': program.start_date and program.start_date.strftime('%d/%m/%Y') or '',
                'end_date': program.end_date and program.end_date.strftime('%d/%m/%Y') or '',
                'company_id': program.company_id.id or 0,
                'company_name': program.company_id.name or '',
                'order_amount': program.order_amount,
                'operator': program.operator or '',
                'reward_type': program.reward_type or '',
                'discount': program.discount,
                'account_id': program.account_id.id or 0,
                'account_name': program.account_id.name or '',
                'product_id': program.product_id.id or 0,
                'product_name': program.product_id.name or '',
                'price_range_based_on': program.price_range_based_on or '',
                'category_ids': [{'id': category.id, 'name': category.complete_name} for category in
                                 program.category_ids],
                'disc_on_combination_qty_total_qty': program.disc_on_combination_qty_total_qty,
                'multi_category_discount_type': program.multi_category_discount_type or '',
                'multi_category_discount': program.multi_category_discount,
                'multi_category_discount_product_id': program.multi_category_discount_product_id.id or 0,
                'multi_category_discount_product_name': program.multi_category_discount_product_id.name or '',
                'lines': lines,
                'write_date': program.write_date.strftime(DEFAULT_SERVER_DATETIME_FORMAT),
            })
        return records

    @http.route('/api/get/sale-stock-return', type='json', auth='none', methods=['POST'], csrf=False)
    def get_sale_stock_returns(self, **kwargs):
        records = []
        params = request.jsonrequest
        uid = request.session.uid
        domain = params.get('domain', '[]')
        if not uid:
            return {'success': False, 'error': 'Invalid cookie.'}
        try:
            domain = eval(domain)
        except Exception as e:
            return {'error': 'Invalid domain.'}
        sale_returns = request.env['sale.stock.return'].with_user(SUPERUSER_ID).search(domain)
        for sale_return in sale_returns:
            records.append({
                'id': sale_return.id,
                'name': sale_return.name or '',
                'reference': sale_return.reference or '',
                'partner_id': sale_return.partner_id.id or 0,
                'partner_name': sale_return.partner_id.name or '',
                'date': sale_return.date.strftime(DEFAULT_SERVER_DATETIME_FORMAT) if sale_return.date else '',
                'team_id': sale_return.team_id.id or 0,
                'team_name': sale_return.team_id.name or '',
                'sale_man_id': sale_return.sale_man_id.id or 0,
                'sale_man_name': sale_return.sale_man_id.name or '',
                'route_plan_id': sale_return.route_plan_id.id or 0,
                'route_plan_name': sale_return.route_plan_id.name or '',
                'type': sale_return.type or '',
                'reason': sale_return.reason or '',
                'remarks': sale_return.remarks or '',
                'state': sale_return.state or '',
            })
        return records

    @http.route('/api/get/stock-lot', type='json', auth='none', methods=['POST'], csrf=False)
    def get_stock_lots(self, **kwargs):
        records = []
        params = request.jsonrequest
        uid = request.session.uid
        domain = params.get('domain', '[]')
        if not uid:
            return {'success': False, 'error': 'Invalid cookie.'}
        try:
            domain = eval(domain)
        except Exception as e:
            return {'error': 'Invalid domain.'}
        stock_lots = request.env['stock.production.lot'].with_user(SUPERUSER_ID).search(domain)
        for lot in stock_lots:
            records.append({
                'id': lot.id,
                'name': lot.name,
                'product_id': lot.product_id.id,
                'product_name': lot.product_id.name,
                'expiration_date': lot.expiration_date and lot.expiration_date.strftime(
                    DEFAULT_SERVER_DATETIME_FORMAT) or '',
                'write_date': lot.write_date.strftime(DEFAULT_SERVER_DATETIME_FORMAT),
            })
        return records
