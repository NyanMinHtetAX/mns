import werkzeug
import json
import jwt
from odoo.addons.web.controllers.main import Session
from odoo import http
from odoo.http import request
from functools import wraps
from odoo import SUPERUSER_ID
from odoo.osv import expression
from odoo.exceptions import UserError, ValidationError
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT, config
from markupsafe import Markup

HEADERS = [('content-type', 'application/json')]


def get_jwt_secret():
    return config['jwt_secret'] or 'SECRET'


def get_jwt_algorithm():
    return config['jwt_secret'] or 'SECRET'


def encode_jwt(payload):
    return jwt.encode(payload, get_jwt_secret(), algorithm=get_jwt_algorithm())


def decode_jwt(hash):
    return jwt.decode(hash, get_jwt_secret(), algorithms=[get_jwt_algorithm()])


def _response(response, status_code=200):
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


def _invalid_domain_response():
    body = {'error': 'Invalid domain.'}
    headers = [
        ('Content-Type', 'application/json; charset=utf-8'),
        ('Content-Length', len(body))
    ]
    return werkzeug.wrappers.Response(body, headers=headers, status=400)


class OdooRest(http.Controller):

    @http.route('/api/auth', type='http', auth='none', methods=['POST'], csrf=False)
    def login(self):
        params = request.params
        username = params.get('username')
        password = params.get('password')
        if username and password:
            Session.authenticate({}, request.session.db, username, password)
            user = request.env.user
            token = encode_jwt({'id': user.id})
            return _response({
                'success': True,
                'message': 'Successfully logged in',
                'user_id': user.id,
                'user_name': user.name,
                'company_id': user.company_id.id,
                'company_name': user.company_id.name,
                'image': user.image_1920 and user.image_1920.decode('utf-8') or '',
                'partner_id': user.partner_id.id,
                'token': token,
            })
        else:
            return _response({'success': False, 'error': 'Missing username or password'})

    @http.route('/api/auth/check-password', type='json', auth='none', methods=['POST'], csrf=False)
    def check_old_password(self):
        params = request.jsonrequest
        old_password = params['old_password']
        user_id = params['user_id']
        user = request.env['res.users'].with_user(SUPERUSER_ID).browse(user_id)
        request.env.cr.execute("SELECT COALESCE(password, '') FROM res_users WHERE id=%s", [user.id])
        [hashed] = request.env.cr.fetchone()
        valid = user._crypt_context().verify(old_password, hashed)
        return {'status': valid}


class OdooRestCreate(http.Controller):

    @http.route('/api/create/<string:model>', type='json', auth='none', methods=['POST'], csrf=False)
    def create_record(self, model, **kwargs):
        values = request.jsonrequest
        record = request.env[model].with_user(SUPERUSER_ID).create(values)
        return {'record_id': record.id}

    @http.route('/api/create/sale-order', type='json', auth='none', methods=['POST'], csrf=False)
    def create_sale_order(self, **kwargs):
        params = request.jsonrequest
        values = {
            'partner_id': params.get('partner_id', False),
            'partner_invoice_id': params.get('partner_invoice_id', False),
            'partner_shipping_id': params.get('partner_shipping_id', False),
            'date_order': params.get('date_order', False),
            'pricelist_id': params.get('pricelist_id', False),
            'currency_id': params.get('currency_id', False),
            'payment_term_id': params.get('payment_term_id', False),
            'user_id': params.get('partner_id', False),
        }
        available_fields = request.env['sale.order'].fields_get_keys()
        available_line_fields = request.env['sale.order.line'].fields_get_keys()
        for field in params:
            if field in available_fields:
                values[field] = params[field]
        company_id = request.env['res.users'].with_user(SUPERUSER_ID).browse(SUPERUSER_ID).company_id.id
        order = request.env['sale.order'].with_user(SUPERUSER_ID).with_company(company_id).create(values)
        order_lines = []
        for product in params['products']:
            line_vals = {
                'name': product['description'],
                'product_id': product['product_id'],
                'product_uom_qty': product['qty'],
                'product_uom': product['uom_id'],
                'price_unit': product['price_unit'],
                'order_id': order.id,
            }
            for line_field in product:
                if line_field in available_line_fields:
                    line_vals[line_field] = product[line_field]
            order_lines.append(line_vals)
        request.env['sale.order.line'].with_user(SUPERUSER_ID).with_company(company_id).create(order_lines)
        return {'success': True, 'order_id': order.id, 'order_ref': order.name}


class OdooRestWrite(http.Controller):

    @http.route('/api/write/<string:model>/<int:record_id>', type='json', auth='none', methods=['POST'], csrf=False)
    def write_model_record(self, model, record_id, **kwargs):
        values = request.jsonrequest
        request.env[model].with_user(SUPERUSER_ID).browse(record_id).write(values)
        return {'success': 1, 'message': 'Successfully write the record.'}


class OdooRestDelete(http.Controller):

    @http.route('/api/delete/<string:model>/<int:record_id>', type='json', auth='none', methods=['POST'], csrf=False)
    def delete_model_record(self, model, record_id, **kwargs):
        request.env[model].with_user(SUPERUSER_ID).browse(record_id).unlink()
        return {'success': 1, 'message': f'Successfully deleted the record with id of {record_id}.'}


class OdooRestRead(http.Controller):

    @http.route('/api/get/township', type='json', auth='none', methods=['POST'], csrf=False)
    def get_townships(self):
        records = []
        params = request.params
        domain = params.get('domain', '[]')
        try:
            domain = eval(domain)
        except Exception as e:
            return _invalid_domain_response()
        townships = request.env['res.township'].with_user(SUPERUSER_ID).search(domain)
        for township in townships:
            records.append({
                'id': township.id,
                'name': township.name or '',
                'zip_code': township.zip or '',
            })
        return records

    @http.route('/api/get/city', type='json', auth='none', methods=['POST'], csrf=False)
    def get_cities(self, **kwargs):
        params = request.params
        domain = params.get('domain', '[]')
        try:
            domain = eval(domain)
        except Exception as e:
            return _invalid_domain_response()
        cities = request.env['res.city'].with_user(SUPERUSER_ID).search(domain)
        records = []
        for city in cities:
            records.append({
                'id': city.id,
                'name': city.name or '',
                'code': city.code or '',
                'state_id': city.state_id.id or -1,
                'state_name': city.state_id.name or '',
                'country_id': city.country_id.id or -1,
                'country_name': city.country_id.name or '',
            })
        return records

    @http.route('/api/get/<string:model>', type='json', auth='none', methods=['POST'], csrf=False)
    def get_model(self, model, **kwargs):
        params = request.jsonrequest
        domain = params.get('domain', '[]')
        try:
            domain = eval(domain)
        except Exception as e:
            return _invalid_domain_response()
        model_records = request.env[model].with_user(SUPERUSER_ID).search(domain)
        records = []
        for model_record in model_records:
            records.append({
                'id': model_record.id,
                'name': model_record.name_get()[0][1] or '',
            })
        return records
