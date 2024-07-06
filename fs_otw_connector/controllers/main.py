import pdb

import werkzeug
import json
import jwt
from functools import wraps
from odoo.addons.web.controllers.main import Session
from odoo import http, fields
from odoo.http import request, route
from odoo import SUPERUSER_ID
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT, config
from markupsafe import Markup
from odoo.osv import expression
from dateutil.relativedelta import relativedelta
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT
from datetime import datetime

HEADERS = [('content-type', 'application/json')]


def get_jwt_secret():
    return config['jwt_secret'] or 'SECRET'


def get_jwt_algorithm():
    return 'HS256'


def encode_jwt(payload):
    return jwt.encode(payload, get_jwt_secret(), algorithm=get_jwt_algorithm())


def decode_jwt(hashcode):
    return jwt.decode(hashcode, get_jwt_secret(), algorithms=[get_jwt_algorithm()])


def _http_response(response, status_code=200):
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


def _json_response(body, status=200):
    headers = [('Content-Type', 'application/json; charset=utf-8')]
    return werkzeug.wrappers.Response(body, headers=headers, status=status)


def _invalid_domain_response():
    body = {'error': 'Invalid domain.'}
    headers = [
        ('Content-Type', 'application/json; charset=utf-8'),
        ('Content-Length', len(body))
    ]
    return werkzeug.wrappers.Response(body, headers=headers, status=400)


def authenticate(func):
    @wraps(func)
    def decorator(inst, **kwargs):
        token = request.httprequest.headers.get('authorization', '').replace('Bearer ', '', 1)
        inst.req_body = request.httprequest.data and json.loads(request.httprequest.data.decode('utf-8')) or {}
        inst.auth_user = inst._authenticate(**kwargs)
        return func(inst, **kwargs)

    return decorator


class OdooRest(http.Controller):

    @route('/api/auth', type='http', auth='none', methods=['POST'], csrf=False)
    def login(self):
        params = request.params
        username = params.get('username')
        password = params.get('password')
        if username and password:
            Session.authenticate({}, request.session.db, username, password)
            user = request.env.user
            token = encode_jwt({'id': user.id})
            return _http_response({
                'success': True,
                'message': 'Successfully logged in',
                'user_id': user.id,
                'user_name': user.name,
                'company_id': user.company_id.id,
                'company_name': user.company_id.name,
                'partner_id': user.partner_id.id,
                'email': user.partner_id.email or '',
                'phone': user.partner_id.phone or '',
                'vehicle_no': user.partner_id.vehicle_no or '',
                'viber_no': user.partner_id.viber_no or '',
                'token': token,
                'image': user.image_1920 and user.image_1920.decode('utf-8') or '',

            })
        else:
            return _http_response({'success': False, 'error': 'Missing username or password'})

    @route('/api/auth/check-password', type='json', auth='none', methods=['POST'], csrf=False)
    def check_old_password(self):
        params = request.jsonrequest
        old_password = params['old_password']
        user_id = params['user_id']
        user = request.env['res.users'].with_user(SUPERUSER_ID).browse(user_id)
        request.env.cr.execute("SELECT COALESCE(password, '') FROM res_users WHERE id=%s", [user.id])
        [hashed] = request.env.cr.fetchone()
        valid = user._crypt_context().verify(old_password, hashed)
        return {'status': valid}

    @route('/api/auth/reset_password', type='json', auth='none', methods=['POST'], csrf=False)
    def reset_password(self):
        params = request.jsonrequest
        new_password = params['new_password']
        user_id = params['user_id']
        user = request.env['res.users'].with_user(SUPERUSER_ID).browse(user_id)
        user.password = new_password
        return ({
            'success': True,
            'message': 'Successfully Changed Password',
        })

    @route('/api/get/customer', type='json', auth='none', methods=['POST'], csrf=False)
    def get_customer(self):
        records = []
        param = request.jsonrequest
        domain = param.get('domain', [])
        if domain:
            try:
                domain = eval(domain)
            except Exception as e:
                return {'Success': False, 'Message': 'Invalid Domain'}
        deli_customer = request.env['delivery.man.picking'].with_user(SUPERUSER_ID).search(domain)
        for rec in deli_customer:
            records.append({
                'id': rec.id,
                'customer_name': rec.customer_id.name or '',
                'customer_code': rec.customer_id.ref or '',
                'township_name': rec.customer_id.township_id.name or '',
                'phone': rec.customer_id.phone or '',
                'street': rec.customer_id.street or '',
                'street2': rec.customer_id.street2 or '',
                'city': rec.customer_id.x_city_id.name or '',
                'partner_latitude': rec.customer_id.partner_latitude or 0.000,
                'partner_longitude': rec.customer_id.partner_longitude or 0.000,
            })
        return records

    @route('/api/get/dmp', type='json', auth='none', methods=['POST'], csrf=False)
    def get_delivery_man_picking(self):
        records = []
        param = request.jsonrequest
        domain = param.get('domain', [])
        if domain:
            try:
                domain = eval(domain)
            except Exception as e:
                return {'Success': False, 'Message': 'Invalid Domain'}
        write_date_data = param.get('write_date', False)
        write_date = False
        if write_date_data:
            date_time_obj = datetime.strptime(write_date_data, '%Y-%m-%d %H:%M:%S')
            write_date = (date_time_obj + relativedelta(seconds=1)).strftime(DEFAULT_SERVER_DATETIME_FORMAT)
            first_time = False
        else:
            first_time = True
        if first_time:
            dmp_line = request.env['delivery.man.picking'].with_user(SUPERUSER_ID).search(domain)
        else:
            domain = expression.AND([domain, [('write_date', '>', write_date),('state','=','assign')]])
            dmp_line = request.env['delivery.man.picking'].with_user(SUPERUSER_ID).search(domain)

        for rec in dmp_line:
            invoice_list = []
            product_lines = []
            back_order_lines = []
            for line in rec.picking_lines:
                product_lines.append(
                    {
                    'id': line.id,
                    'product_id': line.product_id.id or '',
                     'product_name': line.product_id.name or '',
                     'quantity_done': line.quantity_done or 0.00,
                     'uom_id': line.uom_id.name or '',
                     }
                )

            for bol in rec.back_order_lines:
                back_order_lines.append({
                    'product_id': bol.product_id.id or '',
                    'product_name': bol.product_id.name or '',
                    'quantity': bol.product_uom_qty or '',
                    'uom_id': bol.uom_id.name or '',
                    'scheduled_date': bol.date or '',
                })
            for invoice in rec.invoice_ids:
                invoice_list.append({
                    'invoice_id': invoice.id,
                    'invoice_no': invoice.name or '',
                    'invoice_date': invoice.invoice_date or '',
                    'amount_due': invoice.amount_residual or 0.00,
                    'currency_id': invoice.currency_id.name or '',
                    'invoice_date_due': invoice.invoice_date_due or '',
                    'payment_status': invoice.payment_state or '',
                })
                
            if rec.sale_customer_id:
                name = str(rec.sale_customer_id.name)
            else:
                name = ''
            records.append({
                'id': rec.id,
                'dmp_no': rec.reference_no or '',
                'picking_no': rec.picking_id.name or '',
                'delivery_date': rec.delivery_date or '',
                'sale_order_ref': rec.sale_order_id.name or '',
                'state': rec.state,
                'signature': rec.signature or '',
                'delivery_note': rec.delivery_note or '',
                'delivery_remarks': rec.delivery_remarks or '',
                'customer_id': rec.customer_id.id,
                'customer_name': name or '',
                'car_gate': str(rec.customer_id.name) or '',
                'customer_code': rec.customer_id.ref or '',
                # 'customer_image': rec.customer_id.image_1920 and rec.customer_id.image_1920.decode('utf-8') or '',
                'township_name': rec.customer_id.township_id.name or '',
                'phone': rec.customer_id.phone or '',
                'mobile': rec.customer_id.mobile or '',
                'street': rec.customer_id.street or '',
                'street2': rec.customer_id.street2 or '',
                'city': rec.customer_id.x_city_id.name or '',
                'partner_latitude': rec.customer_id.partner_latitude or 0.000,
                'partner_longitude': rec.customer_id.partner_longitude or 0.000,
                'product_lines': product_lines,
                'remaining_products': back_order_lines,
                'invoice_lines': invoice_list,
                'write_date': rec.write_date.strftime(DEFAULT_SERVER_DATETIME_FORMAT),
                'customer_image': '',
            })
        print(len(records))
        return records

    @http.route('/api/get/payment_method', type='json', auth='none', methods=['POST'], csrf=False)
    def get_payment_methods(self, **kwargs):
        params = request.params
        domain = params.get('domain', '[]')
        if domain:
            try:
                domain = eval(domain)
            except Exception as e:
                return {'Success': False, 'Message': 'Invalid Domain'}
        payment_methods = request.env['otw.payment.method'].with_user(SUPERUSER_ID).search(domain)
        records = []
        for payment_method in payment_methods:
            records.append({
                'id': payment_method.id,
                'name': payment_method.name or '',
                'write_date': payment_method.write_date.strftime(DEFAULT_SERVER_DATETIME_FORMAT),
                'journal_id': payment_method.journal_id.id,
                'journal_name': payment_method.journal_id.name or '',
                'is_bank': payment_method.is_bank,
            })
        return records

    @http.route('/api/get/currency', type='json', auth='none', methods=['POST'], csrf=False)
    def get_currencies(self, **kwargs):
        params = request.jsonrequest
        uid = request.session.uid
        domain = params.get('domain', '[]')
        additional_fields = params.get('additional_fields', [])
        if not uid:
            return {'error': 'Invalid cookie.'}
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

    @http.route('/api/get/invoice', type='json', auth='none', methods=['POST'], csrf=False)
    def get_paid_amount(self, **kwargs):

        params = request.jsonrequest
        domain = params.get('domain', '[]')
        today_payment_only = params.get('today_payment_only')
        if domain:
            try:
                domain = eval(domain)
            except Exception as e:
                return {'Success': False, 'Message': 'Invalid Domain'}

        invoices = request.env['account.move'].with_user(SUPERUSER_ID).search(domain)
        records = []
        for invoice in invoices:
            payments = request.env['account.payment'].with_user(SUPERUSER_ID).search([]).filtered(
                lambda payment: invoice.id in payment.reconciled_invoice_ids.ids)
            if today_payment_only:
                payments = payments.filtered(lambda payment: payment.date == fields.Date.today())
            invoice_payments = []
            for payment in payments:
                invoice_payments.append({
                    'payment_id': payment.id,
                    'payment_name': payment.name or '',
                    'payment_date': payment.date,
                    'payment_amount': payment.amount,
                })
            records.append({
                'customer_name': invoice.partner_id.name,
                'customer_id': invoice.partner_id.id,
                'invoice_id': invoice.id,
                'invoice_no': invoice.name or '',
                'invoice_date': invoice.invoice_date or '',
                'amount_due': invoice.amount_residual,
                'currency_id': invoice.currency_id.name or '',
                'payment_status': invoice.payment_state,
                'payments': invoice_payments,
            })
        return records


class OdooRestCreate(http.Controller):

    @http.route('/api/create/<string:model>', type='json', auth='none', methods=['POST'], csrf=False)
    def create_record(self, model, **kwargs):
        model = model.replace('-', '.')
        values = request.jsonrequest
        record = request.env[model].with_user(SUPERUSER_ID).create(values)
        return {'record_id': record.id}

    @http.route('/api/create/device', type='json', auth='none', methods=['POST'], csrf=False)
    def create_device(self, **kwargs):
        values = request.jsonrequest
        record = request.env['delivery.app.device'].with_user(SUPERUSER_ID).search(
            [('device_id', '=', values['device_id'])])
        if not record:
            record = request.env['delivery.app.device'].with_user(SUPERUSER_ID).create(values)
        return {'record_id': record.id}

    @http.route('/api/create/payment', type='json', auth='none', methods=['POST'], csrf=False)
    def create_payment(self, **kwargs):
        param_data = request.jsonrequest
        lines = param_data.get('vals', [])
        images = param_data.get('images', [])

        uid = request.session.uid
        company_id = request.env['res.users'].sudo().browse(uid).company_id.id
        invoice_id = []
        for params in lines:
            partner_id = params['partner_id']
            amount = params['amount']
            date = params['date']
            ref = params['payment_memo']
            invoice_ids = params['invoice_ids']
            invoice_id.append(invoice_ids)
            payment_type = params['payment_type']
            payment_name = params['payment_name']
            journal = request.env['fieldsale.payment.method'].with_user(SUPERUSER_ID).search(
                [('journal_id.type', '=', payment_type), ('name', '=',payment_name)]).journal_id.id
            journal_id = journal

            payment_data = request.env['account.payment'].with_user(SUPERUSER_ID).with_company(company_id).create({
                'payment_type': 'inbound',
                'partner_id': partner_id,
                'amount': amount,
                'date': date,
                'ref': ref,
                'journal_id': journal_id,

            })
            payment_data.action_post()
            payment_lines = payment_data.line_ids
            payment_receivable_account_id = payment_lines.filtered(
                lambda b: b.account_internal_type == 'receivable')
            invoice_data = request.env['account.move'].sudo().browse(invoice_ids)
            line_ids = invoice_data.line_ids
            account_receivable_id = line_ids.filtered(lambda b: b.account_internal_type == 'receivable')
            (payment_receivable_account_id + account_receivable_id).reconcile()
        if images:
            move_id = request.env['account.move'].with_user(SUPERUSER_ID).search([('id', '=', invoice_id[0])])
            move_id.write({
                'payment_attachment_ids': images
            })
        return {'success': 1, 'payment_data_id': payment_data.id}


class OdooRestWrite(http.Controller):

    @http.route('/api/write/profile', type='json', auth='none', methods=['POST'], csrf=False)
    def update_profile(self):
        values = request.jsonrequest
        if 'partner_vals' in values:
            request.env['res.partner'].with_user(SUPERUSER_ID).browse(values['partner_id']).write(
                values['partner_vals'])
        if 'user_vals' in values:
            request.env['res.users'].with_user(SUPERUSER_ID).browse(values['user_id']).write(values['user_vals'])
        return {'success': True}

    @http.route('/api/write/<string:model>/<int:record_id>', type='json', auth='none', methods=['POST'], csrf=False)
    def write_model_record(self, model, record_id, **kwargs):
        model = model.replace('-', '.')
        values = request.jsonrequest
        request.env[model].with_user(SUPERUSER_ID).browse(record_id).write(values)
        return {'success': 1, 'message': 'Successfully write the record.'}

    @route('/api/write/dmp', type='json', auth='none', methods=['POST'], csrf=False)
    def write_dmp(self):

        values = request.jsonrequest
        record = request.env['delivery.man.picking'].with_user(SUPERUSER_ID).browse(values['id'])
        dmp_values = values['vals']
        record.write(dmp_values)
        for rec in values['line_vals']:
            record1 = request.env['picking.line'].with_user(SUPERUSER_ID).browse(rec['id'])
            record1.delivery_picking_id = rec['delivery_picking_id']
            record1.product_id = rec['product_id']
            record1.quantity_done = rec['quantity_done']
            record1.quantity_return = rec['quantity_return']
            record1.partial = rec['partial']
        return {'success': True,
                'message': 'Successfully Write The Record',
                }

    @route('/api/write/dmpline', type='json', auth='none', methods=['POST'], csrf=False)
    def write_dmpline(self):

        values = request.jsonrequest
        record = request.env['picking.line'].with_user(SUPERUSER_ID).browse(values['id'])
        dmp_values = values['vals']
        record.write(dmp_values)
        return {'success': True,
                'message': 'Successfully Write The Record',
                }


class OdooRestDelete(http.Controller):

    @http.route('/api/delete/<string:model>/<int:record_id>', type='json', auth='none', methods=['POST'], csrf=False)
    def delete_model_record(self, model, record_id, **kwargs):
        model = model.replace('-', '.')
        request.env[model].with_user(SUPERUSER_ID).browse(record_id).unlink()
        return {'success': 1, 'message': f'Successfully deleted the record with id of {record_id}.'}


class OdooRestRead(http.Controller):
    pass
