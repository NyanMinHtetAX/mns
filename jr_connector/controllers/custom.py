import werkzeug
import json
from odoo.addons.web.controllers.main import Session
from odoo import http, fields
from odoo.http import request
from functools import wraps
from odoo import SUPERUSER_ID
from odoo.osv import expression
from odoo.exceptions import UserError, ValidationError
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT
from markupsafe import Markup
from datetime import date, datetime, timedelta

HEADERS = [('content-type', 'application/json')]


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


class OdooRest(http.Controller):

    @http.route('/api/auth/just-order', type='http', auth='none', methods=['POST'], csrf=False)
    def login(self, **kwargs):
        params = request.params
        username = params.get('username')
        password = params.get('password')
        if username and password:
            Session.authenticate({}, request.session.db, username, password)
            user = request.env.user
            company_data = request.env['res.company'].with_user(SUPERUSER_ID).search([('id','=',user.company_id.id)])
            jr_data = request.env['jr.config'].with_user(SUPERUSER_ID).search([('company_id','=',user.company_id.id)])
            if user.property_product_pricelist and user.partner_id.property_payment_term_id:
                if user.partner_id.customer:
                    return _response({
                        'success': True,
                        'message': 'Successfully logged in',
                        'user_id': user.id,
                        'user_name': user.name or '',
                        'company_id': user.company_id.id or 0,
                        'company_name': user.company_id.name or '',
                        'country_id': user.partner_id.country_id.id or 0,
                        'country_name': user.partner_id.country_id.name or '',
                        'pricelist': user.partner_id.property_product_pricelist.id or 0,
                        'payment_term_id': user.partner_id.property_payment_term_id.id or 0,
                        'currency_id': user.company_id.currency_id.id or 0,
                        'image': user.image_1920 and user.image_1920.decode('utf-8') or '',
                        'partner_id': user.partner_id.id,
                    })
                else:
                    return _response({
                        'success': True,
                        'message': 'Successfully logged in',
                        'user_id': user.id,
                        'user_name': user.name or '',
                        'company_id': user.company_id.id or 0,
                        'company_name': user.company_id.name or '',
                        'country_id': user.partner_id.country_id.id or 0,
                        'country_name': user.partner_id.country_id.name or '',
                        'pricelist': jr_data.pricelist_id.id or 0,
                        'payment_term_id': user.partner_id.property_payment_term_id.id or 0,
                        'currency_id': user.company_id.currency_id.id or 0,
                        'image': user.image_1920 and user.image_1920.decode('utf-8') or '',
                        'partner_id': user.partner_id.id,
                    })
            else:
                return _response({'success': False, 'error': 'Pricelist or payment term not available in this customer'})
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

    @http.route('/api/auth/check_pricelist', type='json', auth='none', methods=['POST'], csrf=False)
    def check_pricelist(self):
        params = request.jsonrequest
        partner_id = params['partner_id']
        pricelist_id = params['pricelist_id']
        partner_data = request.env['res.partner'].with_user(SUPERUSER_ID).search([('id','=',partner_id),('customer','=',True)])
        if partner_data.property_product_pricelist.id != pricelist_id:
            return {'pricelist_id': partner_data.property_product_pricelist.id}

    @http.route('/api/get/dashboard', type='json', auth='none', methods=['POST'], csrf=False)
    def get_dashboard_data(self):
        records = []
        param = request.jsonrequest
        domain = param.get('domain', [])
        if domain:
            try:
                domain = eval(domain)
            except Exception as e:
                return {'Success': False, 'Message': 'Invalid Domain'}
        customer_domain = [('is_from_mobile', '=', True)]
        new_order_list = ['draft', 'sent']
        customers = request.env['res.partner'].with_user(SUPERUSER_ID).search(customer_domain)
        orders = request.env['sale.order'].with_user(SUPERUSER_ID).search(
            [('is_from_mobile_order', '=', True), ('state', '=', 'sale')])
        new_orders = request.env['sale.order'].with_user(SUPERUSER_ID).search([('is_from_mobile_order', '=', True)])
        wishlists = request.env['jr.wishlist'].with_user(SUPERUSER_ID).search([])
        new_order = new_orders.filtered(lambda b: b.state in new_order_list)
        request._cr.execute('''SELECT  partner_id, SUM(amount_total) FROM account_move WHERE is_from_mobile_order =True
                           GROUP BY partner_id
                           ORDER BY sum(amount_total) DESC
                           limit 10''')
        customer_data = request._cr.dictfetchall()
        top_selling_customer = []
        for rec in customer_data:
            partner_id = rec['partner_id']

            partner_id_obj = request.env['res.partner'].with_user(SUPERUSER_ID).browse(partner_id)
            rec_list = list(rec)
            rec_list[0] = partner_id_obj.name
            top_selling_customer.append({
                'customer': rec_list[0],
                'amount': rec['sum']
            })
        recent_order = []
        for rec in orders:
            recent_order.append({
                'ref': rec.name,
                'order_date': rec.date_order,
            })
        top_selling_customer_year = []
        if 'This Year' in domain:
            today_date = fields.Date.today()
            start_year_date = date(date.today().year, 1, 1)
            request._cr.execute('''SELECT  partner_id, SUM(amount_total) FROM account_move WHERE is_from_mobile_order =True 
                       and state ='posted' and  date >=%s and date<= %s GROUP BY partner_id ORDER BY sum(amount_total) DESC limit 
                       10''', (start_year_date, today_date))
            this_year_order = request._cr.dictfetchall()
            orders = request.env['sale.order'].with_user(SUPERUSER_ID).search(
                [('is_from_mobile_order', '=', True), ('state', '=', 'sale'), ('date_order', '>=', start_year_date),
                 ('date_order', '<=', today_date)])
            new_order_list = ['draft', 'sent']
            new_orders = request.env['sale.order'].with_user(SUPERUSER_ID).search(
                [('is_from_mobile_order', '=', True), ('date_order', '>=', start_year_date),
                 ('date_order', '<=', today_date)])
            new_order = new_orders.filtered(lambda b: b.state in new_order_list)
            customer_domain = [('is_from_mobile', '=', True), ('create_date', '>=', start_year_date),
                               ('create_date', '<=', today_date)]
            customers = request.env['res.partner'].with_user(SUPERUSER_ID).search(customer_domain)

            wishlists = request.env['jr.wishlist'].with_user(SUPERUSER_ID).search(
                [('date', '>=', start_year_date), ('date', '<=', today_date)])
            for rec in this_year_order:
                partner_id = rec['partner_id']

                partner_id_obj = request.env['res.partner'].with_user(SUPERUSER_ID).browse(partner_id)
                rec_list = list(rec)
                rec_list[0] = partner_id_obj.name
                top_selling_customer_year.append({
                    'customer': rec_list[0],
                    'amount': rec['sum'],
                })
            records.append(
                {
                    'total_order': len(orders),
                    'new_order': len(new_order),
                    'total_customer': len(customers),
                    'total_wishlist': len(wishlists),
                    'top_selling_customers': top_selling_customer_year,

                })
        elif 'This Month' in domain:
            today_date = fields.Date.today()
            today = datetime.today()
            current_first_month_day = date(today.year, today.month, 1)
            request._cr.execute('''SELECT  partner_id, SUM(amount_total) FROM account_move WHERE is_from_mobile_order =True 
                             and state ='posted' and date >=%s and date<= %s GROUP BY partner_id ORDER BY sum(amount_total) DESC limit 
                             10''', (current_first_month_day, today_date))
            top_selling_customer_month = []
            this_year_order = request._cr.dictfetchall()
            orders = request.env['sale.order'].with_user(SUPERUSER_ID).search(
                [('is_from_mobile_order', '=', True), ('state', '=', 'sale'),
                 ('date_order', '>=', current_first_month_day),
                 ('date_order', '<=', today_date)])
            new_order_list = ['draft', 'sent']
            new_orders = request.env['sale.order'].with_user(SUPERUSER_ID).search(
                [('is_from_mobile_order', '=', True), ('date_order', '>=', current_first_month_day),
                 ('date_order', '<=', today_date)])
            new_order = new_orders.filtered(lambda b: b.state in new_order_list)
            customer_domain = [('is_from_mobile', '=', True), ('create_date', '>=', current_first_month_day),
                               ('create_date', '<=', today_date)]
            customers = request.env['res.partner'].with_user(SUPERUSER_ID).search(customer_domain)

            wishlists = request.env['jr.wishlist'].with_user(SUPERUSER_ID).search(
                [('date', '>=', current_first_month_day), ('date', '<=', today_date)])
            for rec in this_year_order:
                partner_id = rec['partner_id']

                partner_id_obj = request.env['res.partner'].with_user(SUPERUSER_ID).browse(partner_id)
                rec_list = list(rec)
                rec_list[0] = partner_id_obj.name
                top_selling_customer_month.append({
                    'customer': rec_list[0],
                    'amount': rec['sum'],
                })
            records.append(
                {
                    'total_order': len(orders),
                    'new_order': len(new_order),
                    'total_customer': len(customers),
                    'total_wishlist': len(wishlists),
                    'top_selling_customers': top_selling_customer_month,

                })
        elif 'This Week' in domain:
            today = date.today()
            start = today - timedelta(days=today.weekday())
            end = start + timedelta(days=6)
            request._cr.execute('''SELECT  partner_id, SUM(amount_total) FROM account_move WHERE is_from_mobile_order =True 
                              and state ='posted' and  date >=%s and date<= %s GROUP BY partner_id ORDER BY sum(amount_total) DESC limit 
                              10''', (start, today))
            top_selling_customer_week = []
            this_year_order = request._cr.dictfetchall()
            orders = request.env['sale.order'].with_user(SUPERUSER_ID).search(
                [('is_from_mobile_order', '=', True), ('state', '=', 'sale'), ('date_order', '>=', start),
                 ('date_order', '<=', end)])
            new_order_list = ['draft', 'sent']
            new_orders = request.env['sale.order'].with_user(SUPERUSER_ID).search(
                [('is_from_mobile_order', '=', True), ('date_order', '>=', start),
                 ('date_order', '<=', end)])
            new_order = new_orders.filtered(lambda b: b.state in new_order_list)

            customer_domain = [('is_from_mobile', '=', True), ('create_date', '>=', start), ('create_date', '<=', end)]
            customers = request.env['res.partner'].with_user(SUPERUSER_ID).search(customer_domain)

            wishlists = request.env['jr.wishlist'].with_user(SUPERUSER_ID).search(
                [('date', '<=', end), ('date', '>=', start)])
            for rec in this_year_order:
                partner_id = rec['partner_id']

                partner_id_obj = request.env['res.partner'].with_user(SUPERUSER_ID).browse(partner_id)
                rec_list = list(rec)
                rec_list[0] = partner_id_obj.name
                top_selling_customer_week.append({
                    'customer': rec_list[0],
                    'amount': rec['sum'],
                })
            records.append(
                {
                    'total_order': len(orders),
                    'new_order': len(new_order),
                    'total_customer': len(customers),
                    'total_wishlist': len(wishlists),
                    'top_selling_customers': top_selling_customer_week,
                })
        elif 'Last Month' in domain:

            last_day_of_prev_month = date.today().replace(day=1) - timedelta(days=1)
            start_day_of_prev_month = date.today().replace(day=1) - timedelta(days=last_day_of_prev_month.day)

            request._cr.execute('''SELECT  partner_id, SUM(amount_total) FROM account_move WHERE is_from_mobile_order =True 
                                and state ='posted' and  date >=%s and date<= %s GROUP BY partner_id ORDER BY sum(amount_total) DESC limit 
                                10''', (start_day_of_prev_month, last_day_of_prev_month,))
            top_selling_customer_last_month = []
            this_year_order = request._cr.dictfetchall()
            orders = request.env['sale.order'].with_user(SUPERUSER_ID).search(
                [('is_from_mobile_order', '=', True), ('state', '=', 'sale'),
                 ('date_order', '<=', last_day_of_prev_month),
                 ('date_order', '>=', start_day_of_prev_month)])
            new_order_list = ['draft', 'sent']
            new_orders = request.env['sale.order'].with_user(SUPERUSER_ID).search(
                [('is_from_mobile_order', '=', True), ('date_order', '<=', last_day_of_prev_month),
                 ('date_order', '>=', start_day_of_prev_month)])
            new_order = new_orders.filtered(lambda b: b.state in new_order_list)

            customer_domain = [('is_from_mobile', '=', True), ('create_date', '<=', last_day_of_prev_month),
                               ('create_date', '>=', start_day_of_prev_month)]
            customers = request.env['res.partner'].with_user(SUPERUSER_ID).search(customer_domain)

            wishlists = request.env['jr.wishlist'].with_user(SUPERUSER_ID).search(
                [('date', '<=', last_day_of_prev_month), ('date', '>=', start_day_of_prev_month)])
            for rec in this_year_order:
                partner_id = rec['partner_id']

                partner_id_obj = request.env['res.partner'].with_user(SUPERUSER_ID).browse(partner_id)
                rec_list = list(rec)
                rec_list[0] = partner_id_obj.name
                top_selling_customer_last_month.append({
                    'customer': rec_list[0],
                    'amount': rec['sum'],
                })
            records.append(
                {
                    'total_order': len(orders),
                    'new_order': len(new_order),
                    'total_customer': len(customers),
                    'total_wishlist': len(wishlists),
                    'top_selling_customers': top_selling_customer_last_month,
                })
        else:
            records.append(
                {
                    'total_order': len(orders),
                    'new_order': len(new_order),
                    'total_customer': len(customers),
                    'total_wishlist': len(wishlists),
                    'top_selling_customers': top_selling_customer,
                    'recent_orders': recent_order,
                }
            )
        return records


class OdooRestCreate(http.Controller):

    @http.route('/api/create/<string:model>', type='json', auth='none', methods=['POST'], csrf=False)
    def create_record(self, model, **kwargs):
        values = request.jsonrequest
        record = request.env[model].with_user(SUPERUSER_ID).create(values)
        return {'record_id': record.id}

    @http.route('/api/create/portal-user', type='json', auth='none', methods=['POST'], csrf=False)
    def create_portal_user(self, **kwargs):
        group_internal = request.env.ref('base.group_user')
        group_portal = request.env.ref('base.group_portal')
        group_public = request.env.ref('base.group_public')
        superuser = request.env['res.users'].with_user(SUPERUSER_ID).browse(SUPERUSER_ID)
        params = request.jsonrequest
        name = params['name']
        email = params['email']
        password = params['password']
        ph_number = params['ph_number']
        street = params['shipping_address']
        township_id = int(params['township_id'])
        state_id = int(params['city_id'])
        user_already_exist = request.env['res.users'].search([('login', '=', ph_number)])
        if user_already_exist:
            return {'success': 0, 'error': 'User already exists.'}
        company = params['company_id']
        config_data = request.env['jr.config'].with_user(SUPERUSER_ID).search([('company_id','=',company)])
        country_data = request.env['res.country'].with_user(SUPERUSER_ID).search([('name','=','Myanmar')])
        partner = request.env['res.partner'].with_user(SUPERUSER_ID).with_company(company).create({
            'name': name,
            'email': email,
            'phone': ph_number,
            'street': street,
            'township_id': township_id,
            'x_city_id': state_id,
            'company_id': company,
            'is_from_mobile': True,
            'country_id': country_data.id,
            'property_payment_term_id': config_data.property_payment_term_id.id,
            'customer': False,
        })
        user_sudo = request.env['res.users'].with_user(SUPERUSER_ID).with_company(company).with_context(
            no_reset_password=False).create({
            'name': name,
            'email': email,
            'login': ph_number,
            'partner_id': partner.id,
            'company_id': company,
            'company_ids': [(4, company)],
        })
        user_sudo.write({
            'active': True,
            'groups_id': [(4, group_portal.id), (3, group_public.id), (3, group_internal.id)],
            'password': password,
        })
        return {
            'success': 1,
            'message': 'Successfully signed up.',
            'user_id': user_sudo.id,
            'user_name': user_sudo.name,
            'company_id': user_sudo.company_id.id,
            'company_name': user_sudo.company_id.name,
            'image': user_sudo.image_1920 and user_sudo.image_1920.decode('utf-8') or '',
            'partner_id': user_sudo.partner_id.id,
        }

    @http.route('/api/create/contact', type='json', auth='none', methods=['POST'], csrf=False)
    def create_delivery_contact(self, **kwargs):
        headers = request.httprequest.headers
        params = request.jsonrequest
        uid = headers['uid']
        uid = int(uid)
        user = request.env['res.users'].with_user(uid).browse(uid)
        partner_fields = request.env['res.partner'].fields_get_keys()
        values = {}
        for field in params:
            if field in partner_fields:
                values[field] = params[field]
        contact_data = request.env['res.partner'].with_user(SUPERUSER_ID).with_company(user.company_id.id).create(
            values)
        return {'success': 1, 'created_uid': contact_data.id}

    @http.route('/api/create/sale-order/just-order', type='json', auth='none', methods=['POST'], csrf=False)
    def create_sale_order(self, **kwargs):
        try:
            params = request.jsonrequest
            values = {
                'partner_id': params.get('partner_id', False),
                'partner_invoice_id': params.get('partner_invoice_id', False),
                'partner_shipping_id': params.get('partner_shipping_id', False),
                'date_order': params.get('date_order', False),
                'pricelist_id': params.get('pricelist_id', False),
                'currency_id': params.get('currency_id', False),
                'payment_term_id': params.get('payment_term_id', False),
                'company_id': params.get('company_id',False)
            }
            available_fields = request.env['sale.order'].fields_get_keys()
            available_line_fields = request.env['sale.order.line'].fields_get_keys()
            for field in params:
                if field in available_fields:
                    values[field] = params[field]
            company_id = request.env['res.users'].with_user(SUPERUSER_ID).browse(SUPERUSER_ID).company_id.id

            order_lines = []
            price = False
            order = request.env['sale.order'].with_user(SUPERUSER_ID).with_company(company_id).create(values)
            for product in params['products']:
                multi_uom_line_id_data = request.env['multi.uom.line'].with_user(SUPERUSER_ID).search([('uom_id', '=', product['uom_id']), ('product_tmpl_id', '=', product['product_tmpl_id'])])
                items = request.env['pricelist.item.uom'].sudo().search([('product_id', '=', product['product_id']),
                                                               ('multi_uom_line_id', '=', multi_uom_line_id_data.id),
                                                               ('pricelist_id', '=', values['pricelist_id'])])
                product_qty = product['qty']
                if items:
                    price = product['multi_price_unit']
                else:
                    product_data = request.env['product.template'].sudo().search([('id', '=',product['product_id'])])
                    multi_uom_line_id_data = request.env['multi.uom.line'].sudo().search(
                        [('id', '=', multi_uom_line_id_data.id), ('product_tmpl_id', '=', product['product_tmpl_id'])])

                    price= (product_data.list_price * multi_uom_line_id_data.ratio)

                product_price_unit = product['multi_price_unit'] / multi_uom_line_id_data.ratio
                line_vals = {
                    'name': product['description'],
                    'product_id': product['product_id'],
                    'multi_uom_qty': product['qty'],
                    'product_uom_qty': product_qty,
                    'product_uom': product['uom_id'],
                    'multi_uom_line_id': multi_uom_line_id_data.id,
                    'multi_price_unit': price,
                    'price_unit': product_price_unit,
                    'order_id': order.id
                }
                # for line_field in product:
                #     if line_field in available_line_fields:
                #         line_vals[line_field] = product[line_field]
                
                order_lines.append(line_vals)
            
            so_data = request.env['sale.order.line'].with_user(SUPERUSER_ID).with_company(company_id).create(order_lines)

            request.env['sale.order'].with_user(SUPERUSER_ID).with_company(company_id).search([('id','=',order.id)]).btn_apply_promotion_program()

        except (UserError, ValidationError) as error:
            request.env.cr.rollback()
            return {'success': False, 'error': str(error)}
        except Exception as error:
            return {'success': False, 'error': str(error)}
        return {'success': True, 'order_id': order.id, 'order_ref': order.name}

    @http.route('/api/create/wish-list', type='json', auth='none', methods=['POST'], csrf=False)
    def create_wishlist(self, **kwargs):

        values = request.jsonrequest
        wishlist = request.env['jr.wishlist'].with_user(SUPERUSER_ID).create(values)
        return {'success': 1, 'wishlist_id': wishlist.id}

    @http.route('/api/create/onesignal-token', type='json', auth='none', methods=['POST'], csrf=False)
    def create_onesignal_token(self, **kwargs):
        values = request.jsonrequest
        partner = request.env['res.partner'].with_user(SUPERUSER_ID).browse(values['partner_id'])
        if values['token'] in partner.notification_token_ids.mapped('token'):
            return {'validationIssue': 'Token already exists.'}
        record = request.env['onesignal.token'].with_user(SUPERUSER_ID).create(values)
        return {'record_id': record.id}


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

    @http.route('/api/sale_order_cancel', type='json', auth='none', methods=['POST'], csrf=False)
    def so_cancel(self):
        values = request.jsonrequest
        so_data = request.env['sale.order'].with_user(SUPERUSER_ID).search([('id','=',values['so_id'])])
        if so_data:
            so_data.state = 'cancel'
            return {'success': True}
        else:
            return {'success': False}

    @http.route('/api/write/just-order/<string:model>/<int:record_id>', type='json', auth='none', methods=['POST'], csrf=False)
    def write_model_record(self, model, record_id, **kwargs):
        values = request.jsonrequest
        request.env[model].with_user(SUPERUSER_ID).browse(record_id).write(values)
        return {'success': 1, 'message': 'Successfully write the record.'}


class OdooRestDelete(http.Controller):

    @http.route('/api/delete/<string:model>/<int:record_id>', type='json', auth='none', methods=['POST'], csrf=False)
    def delete_model_record(self, model, record_id, **kwargs):
        request.env[model].with_user(SUPERUSER_ID).browse(record_id).unlink()
        return {'success': 1, 'message': f'Successfully deleted the record with id of {record_id}.'}

    @http.route('/api/del/wish_list/<int:record_id>', type='json', auth='none', methods=['POST'], csrf=False)
    def delete_wish_list(self, record_id, **kwargs):
        del_wish = request.env['jr.wishlist'].with_user(SUPERUSER_ID).search([('product_id','=',record_id)])

        if del_wish:
            del_wish.unlink()
            return {'success': 1, 'message': f'Successfully deleted the record with id of {record_id}.'}
        else:
            return {'success': 0, 'message': f'Product id does not exist in wish list.'}

    @http.route('/api/mass-delete/<string:model>', type='json', auth='none', methods=['POST'], csrf=False)
    def delete_model_records(self, model, **kwargs):
        params = request.jsonrequest
        try:
            domain = eval(params['domain'])
        except KeyError as e:
            return {'success': False, 'message': 'Please add domain in the body.'}
        except Exception as e:
            return {'success': False, 'message': 'Invalid domain.'}
        request.env[model].with_user(SUPERUSER_ID).search(domain).unlink()
        return {'success': 1, 'message': f'Successfully deleted the records.'}


class OdooRestRead(http.Controller):

    @http.route('/api/get/product', type='http', auth='none', methods=['GET', 'POST'], csrf=False)
    def get_product_products(self):
        records = []
        params = request.params
        domain = params.get('domain', [])
        limit = params.get('limit', False)
        if limit:
            limit = int(limit)
        if domain:
            try:
                domain = eval(domain)
                domain = expression.AND([domain, [('avail_in_mobile', '=', 'true'),('jr_config_ids','!=',False)]])
            except Exception as e:
                return {'success': False, 'message': 'Invalid domain!'}
        else:
            domain = [('avail_in_mobile', '=', 'true')]
        products = request.env['product.product'].with_user(SUPERUSER_ID).search(domain, limit=limit, order='id')
        for product in products:
            if product.active == True:
                if product.detailed_type != 'consu':
                    if product.is_publish == True:
                        alt_products = []
                        for alt_product in product.alternative_product_mcom_ids:
                            alt_products.append({
                                'id': alt_product.id,
                                'name': alt_product.name,
                                'list_price': alt_product.list_price or 0.0,
                            })
                        if product.active:
                            product_status = 1
                        else:
                            product_status = 0
                        records.append({
                            'id': product.id,
                            'name': product.name or '',
                            'is_active': product_status,
                            'product_tmpl_id': product.product_tmpl_id.id or -1,
                            'uom_id': product.uom_id.id,
                            'standard_price': product.standard_price or 0.0,
                            'categ_id': product.categ_id.id or -1,
                            'category_id': product.category_id.id or -1,
                            'category_name': product.category_id.name or '',
                            'list_price': product.list_price or 0.0,
                            'internal_ref': product.default_code or '',
                            'description': product.sale_description or '',
                            'show_available_qty': 1 if product.show_available_qty else 0,
                            'available_onhand_limit': product.available_onhand_limit or 0,
                            'out_of_stock': 1 if product.is_continue_selling else 0,
                            'alternative_products': alt_products,
                            'on_hand': product.qty_available,
                            'product_type': product.detailed_type,
                            'tax_ids': [{'id': tax.id, 'name': tax.name} for tax in product.taxes_id]
                        })
        return _response(records)

    @http.route('/api/get/product_archive', type='json', auth='none', methods=['GET', 'POST'], csrf=False)
    def get_product_archive(self):
        records = []
        params = request.jsonrequest
        partner_id = params.get('partner_id')
        domain = params.get('domain', [])
        if domain:
            try:
                domain = eval(domain)
            except Exception as e:
                return {'success': False, 'message': 'Invalid domain!'}
        else:
            domain = [('avail_in_mobile', '=', 'true')]
        sol_data = request.env['sale.order.line'].with_user(SUPERUSER_ID).search([('state','=','sale'),('order_id.partner_id','=',partner_id)])
        products = request.env['product.product'].with_user(SUPERUSER_ID).search([('id','in',sol_data.product_id.ids),('active','=',False)])
        for product in products:
            alt_products = []
            for alt_product in product.alternative_product_mcom_ids:
                alt_products.append({
                    'id': alt_product.id,
                    'name': alt_product.name,
                    'list_price': alt_product.list_price or 0.0,
                })
            if product.active:
                product_status = 1
            else:
                product_status = 0
            records.append({
                'id': product.id,
                'name': product.name or '',
                'is_active': product_status,
                'product_tmpl_id': product.product_tmpl_id.id or -1,
                'uom_id': product.uom_id.id,
                'standard_price': product.standard_price or 0.0,
                'categ_id': product.categ_id.id or -1,
                'category_id': product.category_id.id or -1,
                'category_name': product.category_id.name or '',
                'list_price': product.list_price or 0.0,
                'internal_ref': product.default_code or '',
                'description': product.sale_description or '',
                'show_available_qty': 1 if product.show_available_qty else 0,
                'available_onhand_limit': product.available_onhand_limit or 0,
                'out_of_stock': 1 if product.is_continue_selling else 0,
                'alternative_products': alt_products,
                'on_hand': product.qty_available,
                'product_type': product.detailed_type,
                'tax_ids': [{'id': tax.id, 'name': tax.name} for tax in product.taxes_id]
            })
        return records

    @http.route('/api/get/product_favorite', type='json', auth='none', methods=['GET', 'POST'], csrf=False)
    def get_product_favorite(self):
        records = []
        params = request.jsonrequest
        today = datetime.today().date()
        three_months_ago = today - timedelta(days=90)
        partner_id = params.get('partner_id')
        domain = params.get('domain', [])
        if limit:
            limit = int(limit)
        if domain:
            try:
                domain = eval(domain)
            except Exception as e:
                return {'success': False, 'message': 'Invalid domain!'}
        else:
            domain = [('avail_in_mobile', '=', 'true')]
        sol_data = request.env['sale.order.line'].with_user(SUPERUSER_ID).search([('state','=','sale'),('order_id.partner_id','=',partner_id),('date_order','>=', three_months_ago.strftime('%Y-%m-%d'),('date_order', '<=', today.strftime('%Y-%m-%d')))])
        sorted_sale_order_lines = sol_data.sorted(key=lambda r: r.product_uom_qty, reverse=True) 
        # products = request.env['product.product'].with_user(SUPERUSER_ID).search([('id','in',sol_data.product_id.ids),('active','=',False)])
        for so in sorted_sale_order_lines:
            if so.product_id.active == True:
                records.append({
                    'id': so.product_id.id
                })
        return records

    @http.route('/api/get/product_update', type='http', auth='none', methods=['GET', 'POST'], csrf=False)
    def get_product_products_update(self):
        records = []
        params = request.params
        domain = params.get('domain', [])
        limit = params.get('limit', False)
        fetch_time = params.get('fetch_time')

        if limit:
            limit = int(limit)
        if domain:
            try:
                domain = eval(domain)
                domain = expression.AND([domain, [('avail_in_mobile', '=', 'true')]])
            except Exception as e:
                return {'success': False, 'message': 'Invalid domain!'}
        else:
            domain = [('avail_in_mobile', '=', 'true')]
        products = request.env['product.product'].with_user(SUPERUSER_ID).search([('write_date', '>=', fetch_time)])
        for product in products:
            alt_products = []
            for alt_product in product.alternative_product_mcom_ids:
                alt_products.append({
                    'id': alt_product.id,
                    'name': alt_product.name,
                    'list_price': alt_product.list_price or 0.0,
                })
            records.append({
                'id': product.id,
                'name': product.name or '',
                'product_tmpl_id': product.product_tmpl_id.id or -1,
                'uom_id': product.uom_id.id,
                'standard_price': product.standard_price or 0.0,
                'categ_id': product.categ_id.id or -1,
                'category_id': product.category_id.id or -1,
                'category_name': product.category_id.name or '',
                'list_price': product.list_price or 0.0,
                'internal_ref': product.default_code or '',
                'description': product.sale_description or '',
                'show_available_qty': 1 if product.show_available_qty else 0,
                'available_onhand_limit': product.available_onhand_limit or 0,
                'out_of_stock': 1 if product.is_continue_selling else 0,
                'alternative_products': alt_products,
                'on_hand': product.qty_available,
                'product_type': product.detailed_type,
                'tax_ids': [{'id': tax.id, 'name': tax.name} for tax in product.taxes_id]
            })
        return _response(records)

    @http.route('/product/multiuom/just-order', type='http', auth='none', methods=['GET', 'POST'], csrf=False)
    def get_multi_uom_lines(self, **kwargs):
        values = request.params
        product_id = values.get('product_id', False)
        product_ids = values.get('product_ids', False)
        if product_id:
            products = request.env['product.product'].with_user(SUPERUSER_ID).browse(eval(product_id))
        elif product_ids:
            products = request.env['product.product'].with_user(SUPERUSER_ID).browse(eval(product_ids))
        else:
            products = request.env['product.product'].with_user(SUPERUSER_ID).search([])
        query = """
                    SELECT      LINE.PRODUCT_TMPL_ID,
                                PP.ID AS PRODUCT_ID,
                                UOM.NAME AS UOM_NAME,
                                LINE.ID,
                                LINE.UOM_ID,
                                LINE.IS_DEFAULT_UOM,
                                LINE.RATIO,
                                LINE.REMARK,
                                LINE.PRICE,
                                TO_CHAR(LINE.WRITE_DATE, 'YYYY-MM-DD HH24:MI:SS') AS WRITE_DATE
                    FROM        MULTI_UOM_LINE LINE
                                LEFT JOIN UOM_UOM UOM ON UOM.ID=LINE.UOM_ID
                                LEFT JOIN PRODUCT_TEMPLATE PT ON PT.ID=LINE.PRODUCT_TMPL_ID
                                LEFT JOIN PRODUCT_PRODUCT PP ON PP.PRODUCT_TMPL_ID=PT.ID
                    WHERE       LINE.PRODUCT_TMPL_ID IN %s
                """
        request.env.cr.execute(query, (tuple(products.product_tmpl_id.mapped('id')),))
        records = request.env.cr.dictfetchall()
        if records:
            for i in records:
                if not i['price']:
                    i['price'] = 0.0
                if not i['remark']:
                    i['remark'] = ''
        return _response({'success': True, 'data': records})

    @http.route('/product_archive/multiuom/just-order', type='http', auth='none', methods=['GET', 'POST'], csrf=False)
    def get_multi_uom_lines_archive(self, **kwargs):
        values = request.params
        partner_id = int(values.get('partner_id', False))
        product_id = values.get('product_id', False)
        product_ids = values.get('product_ids', False)
        sol_data = request.env['sale.order.line'].with_user(SUPERUSER_ID).search([('state','=','sale'),('order_id.partner_id','=',partner_id)])
        
        if product_id:
            products = request.env['product.product'].with_user(SUPERUSER_ID).search([('id','in',sol_data.product_id.ids),('active','=',False)])
        
        elif product_ids:
            products = request.env['product.product'].with_user(SUPERUSER_ID).search([('id','in',sol_data.product_id.ids),('active','=',False)])
        else:
            products = request.env['product.product'].with_user(SUPERUSER_ID).search([('id','in',sol_data.product_id.ids),('active','=',False)])

        query = """
                    SELECT      LINE.PRODUCT_TMPL_ID,
                                PP.ID AS PRODUCT_ID,
                                UOM.NAME AS UOM_NAME,
                                LINE.ID,
                                LINE.UOM_ID,
                                LINE.IS_DEFAULT_UOM,
                                LINE.RATIO,
                                LINE.REMARK,
                                LINE.PRICE, 
                                TO_CHAR(LINE.WRITE_DATE, 'YYYY-MM-DD HH24:MI:SS') AS WRITE_DATE
                    FROM        MULTI_UOM_LINE LINE
                                LEFT JOIN UOM_UOM UOM ON UOM.ID=LINE.UOM_ID
                                LEFT JOIN PRODUCT_TEMPLATE PT ON PT.ID=LINE.PRODUCT_TMPL_ID
                                LEFT JOIN PRODUCT_PRODUCT PP ON PP.PRODUCT_TMPL_ID=PT.ID
                    WHERE       LINE.PRODUCT_TMPL_ID IN %s
                """
        request.env.cr.execute(query, (tuple(products.product_tmpl_id.mapped('id')),))
        records = request.env.cr.dictfetchall()
        if records:
            for i in records:
                if not i['price']:
                    i['price'] = 0.0
                if not i['remark']:
                    i['remark'] = ''
        return _response({'success': True, 'data': records})


    @http.route('/api/get/product_1', type='http', auth='none', methods=['GET', 'POST'], csrf=False)
    def get_product_product_1(self):
        records = []
        params = request.params
        domain = params.get('domain', [])
        category_id = params.get('category_id')
        last_id = int(params.get('last_id'))
        limit = params.get('limit', False)
        if limit:
            limit = int(limit)

        if domain:
            try:
                domain = eval(domain)
                domain = expression.AND([domain, [('avail_in_mobile', '=', 'true')]])
            except Exception as e:
                return {'success': False, 'message': 'Invalid domain!'}
        else:
            domain = [('category_id', '=', int(category_id)), ('avail_in_mobile', '=', 'true')]

        products = request.env['product.product'].with_user(SUPERUSER_ID).search(domain, order='id')
        for product in products:
            alt_products = []
            for alt_product in product.alternative_product_mcom_ids:
                alt_products.append({
                    'id': alt_product.id,
                    'name': alt_product.name,
                    'list_price': alt_product.list_price or 0.0,
                })
            if product.image_1920:
                image = product.image_1920.decode('utf-8')
            else:
                image = ''
            records.append({
                'id': product.id,
                'name': product.name or '',
                'product_tmpl_id': product.product_tmpl_id.id or -1,
                'uom_id': product.uom_id.id,
                'standard_price': product.standard_price or 0.0,
                'categ_id': product.categ_id.id or -1,
                'category_id': product.category_id.id or -1,
                'category_name': product.category_id.name or '',
                'list_price': product.list_price or 0.0,
                'internal_ref': product.default_code or '',
                'description': product.sale_description or '',
                'show_available_qty': 1 if product.show_available_qty else 0,
                'available_onhand_limit': product.available_onhand_limit or 0,
                'out_of_stock': 1 if product.is_continue_selling else 0,
                'alternative_products': alt_products,
                'on_hand': product.qty_available or 0,
                'product_type': product.detailed_type,
                'tax_ids': [{'id': tax.id, 'name': tax.name} for tax in product.taxes_id]
            })
        if last_id == 0:

            return _response(records)
        else:
            index_no = next((index for (index, d) in enumerate(records) if d["product_tmpl_id"] == last_id), None)

            index_no = index_no + 1
            for i in range(index_no):
                del records[0]
            # for i in records:
            #     if i.product_id == last_id:
            if len(records) >= limit:
                limit = len(records)
                split_records = records[:limit]
            else:
                split_records = records[:limit]
            return _response(split_records)

    @http.route('/api/get/product_image_1', type='http', auth='none', methods=['GET', 'POST'], csrf=False)
    def get_product_image_1(self):
        records = []
        params = request.params
        domain = params.get('domain', [])
        category_id = params.get('category_id')
        last_id = int(params.get('last_id'))
        limit = params.get('limit', False)
        if limit:
            limit = int(limit)

        if domain:
            try:
                domain = eval(domain)
                domain = expression.AND([domain, [('avail_in_mobile', '=', 'true')]])
            except Exception as e:
                return {'success': False, 'message': 'Invalid domain!'}
        else:
            domain = [('category_id', '=', int(category_id)), ('avail_in_mobile', '=', 'true')]

        products = request.env['product.product'].with_user(SUPERUSER_ID).search(domain, order='id')
        for product in products:
            if product.image_1920:
                image = product.image_1920.decode('utf-8')
            else:
                image = ''
            records.append({
                'id': product.id,
                'image': image,
            })
        if last_id == 0:

            return _response(records)
        else:
            index_no = next((index for (index, d) in enumerate(records) if d["product_tmpl_id"] == last_id), None)

            index_no = index_no + 1
            for i in range(index_no):
                del records[0]
            # for i in records:
            #     if i.product_id == last_id:
            if len(records) >= limit:
                limit = len(records)
                split_records = records[:limit]
            else:
                split_records = records[:limit]
            return _response(split_records)

    @http.route('/api/get/product-image', type='json', auth='none', methods=['POST'], csrf=False)
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

    @http.route('/api/get/product-multi-image', type='json', auth='none', methods=['GET', 'POST'], csrf=False)
    def get_product_multi_images(self, **kwargs):
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
            images = []
            for multi_image in product.product_mcom_image_ids:
                images.append(multi_image.image_1920.decode('utf-8') if multi_image.image_1920 else '')
            records.append({
                'id': product.id,
                'images': images,
            })
        return records

    @http.route('/api/reset_password', type='json', auth='none', methods=['GET', 'POST'], csrf=False)
    def user_reset_password(self, **kwargs):
        records = []
        params = request.jsonrequest
        domain = params.get('domain', '[]')
        user_name = params.get('user_name', False)
        password = params.get('password', False)
        user_data = request.env['res.users'].sudo().search([('login','=',user_name)])
        if domain:
            try:
                domain = eval(domain)
            except Exception as e:
                return {'success': False, 'message': 'Invalid domain!'}
        # request.env.cr.execute("SELECT COALESCE(password, '') FROM res_users WHERE id=%s", [user.id])
        # [hashed] = request.env.cr.fetchone()
        # valid = user._crypt_context().verify(old_password, hashed)      
        msg ='Resetting Password Completed'

        try:
            user_data.write({
                'password': password,
            })
            return ({'success': True, 'data': msg})
        except:
            msg = "Reset password failed"
            return ({'success': False, 'data': msg})

    @http.route('/api/check_login', type='json', auth='none', methods=['GET', 'POST'], csrf=False)
    def check_login(self, **kwargs):
        records = []
        params = request.jsonrequest
        domain = params.get('domain', '[]')
        user_name = params.get('user_name', False)
        user_data = request.env['res.users'].sudo().search([('login','=',user_name)])
        if user_data:
            return ({'success': True, 'data': 'User Account Valid'})
        else:
            return ({'success': False, 'data': 'User Account Invalid'})

    @http.route('/api/get/company_list', type='json', auth='none', methods=['GET', 'POST'], csrf=False)
    def get_company_list(self, **kwargs):
        records = []
        params = request.jsonrequest
        domain = params.get('domain', '[]')
        if domain:
            try:
                domain = eval(domain)
            except Exception as e:
                return {'success': False, 'message': 'Invalid domain!'}
        companies = request.env['res.company'].with_user(SUPERUSER_ID).search([])
        for company in companies:
            records.append({
                'company_id': company.id,
                'company_name': company.name,
            })
        return records

    @http.route('/api/get/tax', type='json', auth='none', methods=['POST'], csrf=False)
    def get_taxes(self, **kwargs):
        params = request.jsonrequest
        domain = params.get('domain', '[]')
        try:
            domain = eval(domain)
        except Exception as e:
            return {'error': 'Invalid domain.'}
        taxes = request.env['account.tax'].with_user(SUPERUSER_ID).search(domain)
        records = []
        for tax in taxes:
            records.append({
                'id': tax.id,
                'name': tax.name,
                'amount': tax.amount,
                'price_include': tax.price_include,
            })
        return records

    @http.route('/api/get/product-category', type='http', auth='none', methods=['GET', 'POST'], csrf=False)
    def get_product_category(self):
        records = []
        params = request.params
        domain = params.get('domain', [])
        if domain:
            try:
                domain = eval(domain)
            except Exception as e:
                return {'success': False, 'message': 'Invalid domain!'}
        categories = request.env['jr.category'].with_user(SUPERUSER_ID).search(domain)
        for category in categories:
            records.append({
                'id': category.id,
                'name': category.name,
                'parent_id': category.parent_id.id or -1,
                'image_128': category.image_128.decode('utf-8') if category.image_128 else ''
            })
        return _response(records)

    @http.route('/api/get/product-price-list', type='http', auth='none', methods=['GET', 'POST'], csrf=False)
    def get_sale_price_lists(self, **kwargs):
        params = request.params
        domain = params.get('domain', '[]')
        try:
            domain = eval(domain)
        except Exception as e:
            return _response({'error': 'Invalid domain.'}, status_code=400)
        price_lists = request.env['product.pricelist'].with_user(SUPERUSER_ID).search(domain)
        records = []
        for price_list in price_lists:
            items = []
            for item in price_list.item_ids:
                items.append({
                    'compute_price': item.compute_price or '',
                    'applied_on': item.applied_on or '',
                    'category_id': item.categ_id.id or 0,
                    'product_tmpl_id': item.product_tmpl_id.id or 0,
                    'product_id': item.product_id.id or 0,
                    'min_quantity': item.min_quantity,
                    'date_start': item.date_start and item.date_start.strftime(DEFAULT_SERVER_DATETIME_FORMAT) or '',
                    'date_end': item.date_end and item.date_end.strftime(DEFAULT_SERVER_DATETIME_FORMAT) or '',
                    'fixed_price': item.fixed_price,
                    'percent_price': item.percent_price,
                    'base': item.base or 0,
                    'price_discount': item.price_discount,
                    'price_surcharge': item.price_surcharge,
                    'price_round': item.price_round,
                    'price_min_margin': item.price_min_margin,
                    'price_max_margin': item.price_max_margin,
                    'base_pricelist_id': item.base_pricelist_id.id or 0,
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
                    'product.product_pricelist_setting')
            })
        return _response(records)

    @http.route('/api/get/product-price-list-uom', type='http', auth='none', methods=['GET', 'POST'], csrf=False)
    def get_sale_price_lists_uom(self, **kwargs):

        params = request.params
        domain = params.get('domain', '[]')
        try:
            domain = eval(domain)
        except Exception as e:
            return _response({'error': 'Invalid domain.'}, status_code=400)
        price_lists = request.env['product.pricelist'].with_user(SUPERUSER_ID).search(domain)

        records = []
        for price_list in price_lists:
            items = []
            for item in price_list.item_ids:
                items.append({
                    'compute_price': item.compute_price or '',
                    'applied_on': item.applied_on or '',
                    'category_id': item.categ_id.id or 0,
                    'product_tmpl_id': item.product_tmpl_id.id or 0,
                    'product_id': item.product_id.id or 0,
                    'min_quantity': item.min_quantity,
                    'date_start': item.date_start and item.date_start.strftime(DEFAULT_SERVER_DATETIME_FORMAT) or '',
                    'date_end': item.date_end and item.date_end.strftime(DEFAULT_SERVER_DATETIME_FORMAT) or '',
                    'fixed_price': item.fixed_price,
                    'percent_price': item.percent_price,
                    'base': item.base or 0,
                    'price_discount': item.price_discount,
                    'price_surcharge': item.price_surcharge,
                    'price_round': item.price_round,
                    'price_min_margin': item.price_min_margin,
                    'price_max_margin': item.price_max_margin,
                    'base_pricelist_id': item.base_pricelist_id.id or 0,
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
                    'product.product_pricelist_setting')
            })
        return _response(records)

    @http.route('/api/get/sale-order', type='http', auth='none', methods=['GET', 'POST'], csrf=False)
    def get_sale_orders(self, **kwargs):
        params = request.params
        order_id = params.get('order_id', False)
        partner_id = params.get('partner_id', False)
        domain = []
        if order_id:
            order_id = eval(order_id)
            if isinstance(order_id, int):
                order_id = [order_id]
            domain = expression.AND([domain, [('id', 'in', order_id)]])
        if partner_id:
            partner_id = eval(partner_id)
            if isinstance(partner_id, int):
                partner_id = [partner_id]
            domain = expression.AND([domain, [('partner_id', 'in', partner_id)]])
        orders = request.env['sale.order'].with_user(SUPERUSER_ID).search(domain)
        records = []
        for order in orders:
            order_lines = []
            for line in order.order_line:
                multi_uom_line_id_data = request.env['multi.uom.line'].with_user(SUPERUSER_ID).search([('id', '=', line.multi_uom_line_id.id), ('product_tmpl_id', '=', line.product_id.product_tmpl_id.id)])

                order_lines.append({
                    'name': line.name,
                    'product_id': line.product_id.id,
                    'product_uom_qty': line.multi_uom_qty,
                    'product_uom': multi_uom_line_id_data.uom_id.id or 0,
                    'price_unit': line.multi_price_unit,
                    'is_foc': line.is_foc or False,
                })
            picking_data =  request.env['stock.picking'].sudo().search([('sale_id','=',order.id)])
            
            if picking_data:
                picking_data = picking_data[0]
                if order.state == "cancel":
                    state = "Canceled"
                elif order.state != "sale":
                    state = "Order Placed"
                elif order.state == "sale" and picking_data.state == "done":
                    state = "Delivered"
                elif order.state == "sale" and picking_data.state == "waiting":
                    state = "Processing"
                elif order.state == "sale":
                    state = "Confirmed"
            else:
                if order.state == "cancel":
                    state = "Canceled"
                elif order.state != "sale":
                    state = "Order Placed"
                elif order.state == "sale":
                    state = "Confirmed"

            records.append({
                'name': order.name or '',
                'partner_id': order.partner_id.id,
                'partner_invoice_id': order.partner_invoice_id.id,
                'partner_shipping_id': order.partner_shipping_id.id,
                'date_order': order.date_order.strftime('%Y-%m-%d %H:%M:%S') if order.date_order else '',
                'pricelist_id': order.pricelist_id.id,
                'currency_id': order.currency_id.id,
                'payment_term_id': order.payment_term_id.id or -1,
                'warehouse_id': order.warehouse_id.id,
                'user_id': order.user_id.id or -1,
                'team_id': order.team_id.id or -1,
                'order_lines': order_lines,
                'order_id': order.id,
                'state': state,
                'delivery_note': order.delivery_note or '',
            })
        return _response(records)

    @http.route('/api/get/jr-config', type='http', auth='none', methods=['GET', 'POST'], csrf=False)
    def get_jr_config(self, **kwargs):
        records = []
        param = request.params
        domain = param.get('domain', [])
        if domain:
            try:
                domain = eval(domain)
            except Exception as e:
                return {'Success': False, 'Message': 'Invalid Domain'}
        setting_data = request.env['jr.config'].with_user(SUPERUSER_ID).search(domain)
        for rec in setting_data:
            banner_image = []
            for image in rec.product_mcom_image_ids:    
                if image.image_1920:
                    banner_image.append(image.image_1920.decode('utf-8'))
            records.append({
                'id': rec.id,
                'app_name': rec.app_name or '',
                'shop_name': rec.shop_name or '',
                'color': rec.color or '',
                'pricelist': rec.pricelist_id.id or '',
                'working_hour': rec.working_hour or '',
                'ph_no': rec.ph_no or '',
                'remark': rec.remark or '',
                'phone': rec.phone or '',
                'address': rec.address or '',
                'description': rec.description or '',
                'term_and_condition': rec.term_and_condition or '',
                'banner_image': banner_image,
                'logo': rec.image_1920 and rec.image_1920.decode('utf-8') or '',

            })
        return _response(records)

    @http.route('/api/get/delivery-method', type='http', auth='none', methods=['GET', 'POST'], csrf=False)
    def get_delivery_methods(self, **kwargs):
        params = request.params
        domain = params.get('domain', '[]')
        try:
            domain = eval(domain)
        except Exception as e:
            return _response({'error': 'Invalid domain!'}, status_code=400)
        records = []
        delivery_methods = request.env['delivery.carrier'].with_user(SUPERUSER_ID).search(domain)
        for delivery_method in delivery_methods:
            records.append({
                'id': delivery_method.id,
                'name': delivery_method.name,
                'delivery_type': delivery_method.delivery_type,
                'product_id': delivery_method.product_id.id,
                'margin': delivery_method.margin,
                'free_over': delivery_method.free_over,
                'amount': delivery_method.amount,
                'township_id': delivery_method.township_id.ids,
                'city_id': delivery_method.city_id.ids,
                'country_id': delivery_method.country_id.id or -1,
                'description': delivery_method.description or '',
                'fixed_price': delivery_method.fixed_price,
            })
        return _response(records)

    @http.route('/api/get/wish-list', type='http', auth='none', methods=['GET', 'POST'], csrf=False)
    def get_wishlist(self, **kwargs):
        params = request.params
        domain = params.get('domain', '[]')
        try:
            domain = eval(domain)
        except Exception as e:
            return _response({'error': 'Invalid domain.'}, status_code=400)
        wishlists = request.env['jr.wishlist'].with_user(SUPERUSER_ID).search(domain)
        records = []
        for wishlist in wishlists:
            records.append({
                'id': wishlist.id,
                'product_id': wishlist.product_id.id,
                'customer_id': wishlist.customer_id.id,
                'date': wishlist.date and wishlist.date.strftime('%Y-%m-%d') or '',
            })
        return _response(records)

    @http.route('/api/get/township', type='http', auth='none', methods=['GET', 'POST'], csrf=False)
    def get_townships(self):
        records = []
        params = request.params
        domain = params.get('domain', [])
        if domain:
            try:
                domain = eval(domain)
            except Exception as e:
                return {'success': False, 'message': 'Invalid domain!'}
        townships = request.env['res.township'].with_user(SUPERUSER_ID).search(domain)
        for township in townships:
            records.append({
                'id': township.id,
                'name': township.name or '',
                'zip_code': township.zip or '',
                'city_id': township.city_id.id or -1,
                'city_name': township.city_id.name or '',
            })
        return _response(records)

    @http.route('/api/get/city', type='http', auth='none', methods=['GET', 'POST'], csrf=False)
    def get_cities(self, **kwargs):
        params = request.params
        domain = params.get('domain', '[]')
        try:
            domain = eval(domain)
        except Exception as e:
            return _response({'error': 'Invalid domain.'}, status_code=400)
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
        return _response(records)

    @http.route('/api/get/state', type='http', auth='none', methods=['GET', 'POST'], csrf=False)
    def get_states(self, **kwargs):
        params = request.params
        domain = params.get('domain', '[]')
        try:
            domain = eval(domain)
        except Exception as e:
            return _response({'error': 'Invalid domain.'}, status_code=400)
        states = request.env['res.country.state'].with_user(SUPERUSER_ID).search(domain)
        records = []
        for state in states:
            records.append({
                'id': state.id,
                'name': state.name or '',
                'code': state.code or '',
                'country_id': state.country_id.id or -1,
                'country_name': state.country_id.name or '',
            })
        return _response(records)

    @http.route('/api/get/contact', type='http', auth='none', methods=['GET', 'POST'], csrf=False)
    def get_contacts(self):
        params = request.params
        domain = params.get('domain', '[]')
        try:
            domain = eval(domain)
        except Exception as e:
            return _response({'error': 'Invalid domain.'}, status_code=400)
        partners = request.env['res.partner'].with_user(SUPERUSER_ID).search(domain)
        records = []
        for partner in partners:
            delivery_addresses = []
            for address in partner.child_ids.filtered(lambda p: p.type == 'delivery'):
                delivery_addresses.append({
                    'id': address.id,
                    'name': address.name or '',
                    'street': address.street or '',
                    'street2': address.street2 or '',
                    'township_id': address.township_id.id or -1,
                    'township_name': address.township_id.name or '',
                    'city_id': address.x_city_id.id or -1,
                    'city_name': address.x_city_id.name or '',
                    'state_id': address.state_id.id or -1,
                    'state_name': address.state_id.name or '',
                    'country_id': address.country_id.id or -1,
                    'country_name': address.country_id.name or '',
                    'phone': address.phone or '',
                    'mobile': address.mobile or '',
                    'email': address.email or '',
                    'note': address.comment and Markup(address.comment).striptags() or '',
                    'delivery_type': address.delivery_type or '',
                })
            records.append({
                'id': partner.id,
                'name': partner.name or '',
                'ref': partner.ref or '',
                'street': partner.street or '',
                'street2': partner.street2 or '',
                'township_id': partner.township_id.id or -1,
                'township_name': partner.township_id.name or '',
                'city_id': partner.x_city_id.id or -1,
                'city_name': partner.x_city_id.name or '',
                'state_id': partner.state_id.id or -1,
                'state_name': partner.state_id.name or '',
                'company_id': partner.company_id.id or -1,
                'company_name': partner.company_id.name or '',
                'country_id': partner.country_id.id or -1,
                'country_name': partner.country_id.name or '',
                'phone': partner.phone or '',
                'mobile': partner.mobile or '',
                'email': partner.email or '',
                'note': partner.comment and Markup(partner.comment).striptags() or '',
                'pricelist_id': partner.property_product_pricelist.id or -1,
                'pricelist_name': partner.property_product_pricelist.name or '',
                'delivery_carrier_id': partner.property_delivery_carrier_id.id or -1,
                'delivery_carrier_name': partner.property_delivery_carrier_id.name or '',
                'payment_term_id': partner.property_payment_term_id.id or -1,
                'payment_term_name': partner.property_payment_term_id.name or '',
                'delivery_addresses': delivery_addresses,
            })
        return _response(records)

    @http.route('/api/get/<string:model>', type='http', auth='none', methods=['GET', 'POST'], csrf=False)
    def get_model(self, model, **kwargs):

        params = request.params
        domain = params.get('domain', '[]')
        try:
            domain = eval(domain)
        except Exception as e:
            return _response({'error': 'Invalid domain.'}, status_code=400)
        model_records = request.env[model].with_user(SUPERUSER_ID).search(domain)
        records = []
        for model_record in model_records:
            records.append({
                'id': model_record.id,
                'name': model_record.name_get()[0][1] or '',
            })
        return _response(records)

    @http.route('/api/get/promotion-program/just-order', type='json', auth='none', methods=['POST'], csrf=False)
    def get_promotion_programs(self, **kwargs):
        records = []
        params = request.jsonrequest
        uid = request.session.uid
        domain = params.get('domain', '[]')
        try:
            domain = eval(domain)
        except Exception as e:
            return {'error': 'Invalid domain.'}
        programs = request.env['promotion.program'].with_user(SUPERUSER_ID).search(domain)
        for program in programs:
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
                        'product_ids': [{'product_id': product.id, 'name': product.name} for product in line.product_ids],
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
                        'product_ids': [{'product_id': product.id, 'name': product.name} for product in line.product_ids],
                        'line_id': line.id,
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
                'promo_id': program.id,
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
                'category_ids': [{'category_id': category.id, 'name': category.name} for category in
                                 program.category_ids],
                'disc_on_combination_qty_total_qty': program.disc_on_combination_qty_total_qty,
                'multi_category_discount_type': program.multi_category_discount_type or '',
                'multi_category_discount': program.multi_category_discount,
                'multi_category_discount_product_id': program.multi_category_discount_product_id.id or 0,
                'multi_category_discount_product_name': program.multi_category_discount_product_id.name or '',
                'lines': lines,
            })
        return records
