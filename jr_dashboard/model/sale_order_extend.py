from odoo import models, fields, api, _
from datetime import date, datetime, timedelta


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    @api.model
    def get_total_jr_order(self):
        customer_domain = [('is_from_mobile', '=', True)]
        new_order_list = ['draft', 'sent']
        customers = self.env['res.partner'].search(customer_domain)
        orders = self.env['sale.order'].search([('is_from_mobile_order', '=', True), ('state', '=', 'sale')])
        new_orders = self.env['sale.order'].search([('is_from_mobile_order', '=', True)])
        wishlists = self.env['jr.wishlist'].search([])
        new_order = new_orders.filtered(lambda b: b.state in new_order_list)

        self._cr.execute('''SELECT  partner_id, SUM(amount_total) FROM account_move WHERE is_from_mobile_order =True
           GROUP BY partner_id
           ORDER BY sum(amount_total) DESC
           limit 1''')
        customer_data = self._cr.dictfetchall()
        # ___________________________________________________
        top_selling_customer = []

        for rec in customer_data:
            partner_id = rec['partner_id']

            partner_id_obj = self.env['res.partner'].browse(partner_id)
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
        return {
            'recent_order': recent_order,
            'customers': top_selling_customer,
            'total_order': len(orders),
            'new_order': len(new_order),
            'total_customer': len(customers),
            'total_wishlist': len(wishlists)
        }

    def get_total_order(self):
        orders = self.env['sale.order'].search([('is_from_mobile_order', '=', True), ('state', '=', 'sale')])
        return {
            'total_order': len(orders),

        }

    def get_new_order(self):
        new_order_list = ['draft', 'sent']
        new_orders = self.env['sale.order'].search([('is_from_mobile_order', '=', True)])
        new_order = new_orders.filtered(lambda b: b.state in new_order_list)
        return {
            'new_order': len(new_order),
        }

    def get_total_customer(self):
        customer_domain = [('is_from_mobile', '=', True)]
        customers = self.env['res.partner'].search(customer_domain)
        return {
            'total_customer': len(customers),
        }

    def get_total_wishlist(self):
        wishlists = self.env['jr.wishlist'].search([])
        return {
            'total_wishlist': len(wishlists),
        }

    def get_top_selling_customer(self):
        self._cr.execute('''SELECT  partner_id, SUM(amount_total) FROM account_move WHERE is_from_mobile_order =True 
        and state='posted' GROUP BY partner_id ORDER BY sum(amount_total) DESC limit 10''')
        customer_data = self._cr.dictfetchall()

        top_selling_customer = []

        for rec in customer_data:
            partner_id = rec['partner_id']

            partner_id_obj = self.env['res.partner'].browse(partner_id)
            rec_list = list(rec)
            rec_list[0] = partner_id_obj.name
            top_selling_customer.append({
                'customer': rec_list[0],
                'amount': rec['sum']
            })
        return {
            'top_selling_customer': top_selling_customer,
        }

    def get_recent_order(self):
        today = date.today()
        start_date = today - timedelta(days=7)
        orders = self.env['sale.order'].search(
            [('is_from_mobile_order', '=', True), ('state', '=', 'sale'), ('date_order', '>=', start_date),
             ('date_order', '<=', today)], limit=30)
        recent_order = []
        for rec in orders:
            recent_order.append({
                'ref': rec.name,
                'order_date': rec.date_order,
            })
        return {
            'recent_order': recent_order,
        }

    def get_this_year(self):
        today_date = fields.Date.today()
        start_year_date = date(date.today().year, 1, 1)
        self._cr.execute('''SELECT  partner_id, SUM(amount_total) FROM account_move WHERE is_from_mobile_order =True 
        and state ='posted' and  date >=%s and date<= %s GROUP BY partner_id ORDER BY sum(amount_total) DESC limit 
        10''', (start_year_date, today_date))
        # THIS YEAR ORDER
        this_year_order = self._cr.dictfetchall()
        orders = self.env['sale.order'].search(
            [('is_from_mobile_order', '=', True), ('state', '=', 'sale'), ('date_order', '>=', start_year_date),
             ('date_order', '<=', today_date)])
        # THIS YEAR NEW ORDER
        new_order_list = ['draft', 'sent']
        new_orders = self.env['sale.order'].search(
            [('is_from_mobile_order', '=', True), ('date_order', '>=', start_year_date),
             ('date_order', '<=', today_date)])
        new_order = new_orders.filtered(lambda b: b.state in new_order_list)

        # THIS YEAR NEW CUSTOMER
        customer_domain = [('is_from_mobile', '=', True), ('create_date', '>=', start_year_date),
                           ('create_date', '<=', today_date)]
        customers = self.env['res.partner'].search(customer_domain)

        wishlists = self.env['jr.wishlist'].search([('date', '>=', start_year_date), ('date', '<=', today_date)])

        top_selling_customer = []
        for rec in this_year_order:
            partner_id = rec['partner_id']

            partner_id_obj = self.env['res.partner'].browse(partner_id)
            rec_list = list(rec)
            rec_list[0] = partner_id_obj.name
            top_selling_customer.append({
                'customer': rec_list[0],
                'amount': rec['sum'],
            })

        return {
            'total_wishlist': len(wishlists),
            'total_order': len(orders),
            'new_order': len(new_order),
            'total_customer': len(customers),
            'time_range': 'this_year',
            'top_selling_customer': top_selling_customer,
        }

    def get_this_month(self):
        today_date = fields.Date.today()
        today = datetime.today()
        current_first_month_day = date(today.year, today.month, 1)
        self._cr.execute('''SELECT  partner_id, SUM(amount_total) FROM account_move WHERE is_from_mobile_order =True 
              and state ='posted' and date >=%s and date<= %s GROUP BY partner_id ORDER BY sum(amount_total) DESC limit 
              10''', (current_first_month_day, today_date))
        top_selling_customer = []
        # THIS MONTH ORDER
        this_year_order = self._cr.dictfetchall()
        orders = self.env['sale.order'].search(
            [('is_from_mobile_order', '=', True), ('state', '=', 'sale'), ('date_order', '>=', current_first_month_day),
             ('date_order', '<=', today_date)])
        # THIS MONTH NEW ORDER
        new_order_list = ['draft', 'sent']
        new_orders = self.env['sale.order'].search(
            [('is_from_mobile_order', '=', True), ('date_order', '>=', current_first_month_day),
             ('date_order', '<=', today_date)])
        new_order = new_orders.filtered(lambda b: b.state in new_order_list)

        # THIS MONTH NEW CUSTOMER
        customer_domain = [('is_from_mobile', '=', True), ('create_date', '>=', current_first_month_day),
                           ('create_date', '<=', today_date)]
        customers = self.env['res.partner'].search(customer_domain)

        wishlists = self.env['jr.wishlist'].search(
            [('date', '>=', current_first_month_day), ('date', '<=', today_date)])
        for rec in this_year_order:
            partner_id = rec['partner_id']

            partner_id_obj = self.env['res.partner'].browse(partner_id)
            rec_list = list(rec)
            rec_list[0] = partner_id_obj.name
            top_selling_customer.append({
                'customer': rec_list[0],
                'amount': rec['sum'],
            })
        return {
            'total_wishlist': len(wishlists),
            'total_order': len(orders),
            'new_order': len(new_order),
            'total_customer': len(customers),
            'time_range': 'this_month',
            'top_selling_customer': top_selling_customer,
        }

    def get_this_week(self):

        today = date.today()

        start = today - timedelta(days=today.weekday())

        end = start + timedelta(days=6)

        self._cr.execute('''SELECT  partner_id, SUM(amount_total) FROM account_move WHERE is_from_mobile_order =True 
              and state ='posted' and  date >=%s and date<= %s GROUP BY partner_id ORDER BY sum(amount_total) DESC limit 
              10''', (start, today))
        top_selling_customer = []
        # THIS MONTH ORDER
        this_year_order = self._cr.dictfetchall()
        orders = self.env['sale.order'].search(
            [('is_from_mobile_order', '=', True), ('state', '=', 'sale'), ('date_order', '>=', start),
             ('date_order', '<=', end)])
        # THIS MONTH NEW ORDER
        new_order_list = ['draft', 'sent']
        new_orders = self.env['sale.order'].search(
            [('is_from_mobile_order', '=', True), ('date_order', '>=', start),
             ('date_order', '<=', end)])
        new_order = new_orders.filtered(lambda b: b.state in new_order_list)

        # THIS MONTH NEW CUSTOMER
        customer_domain = [('is_from_mobile', '=', True), ('create_date', '>=', start), ('create_date', '<=', end)]
        customers = self.env['res.partner'].search(customer_domain)

        wishlists = self.env['jr.wishlist'].search(
            [('date', '<=', end), ('date', '>=', start)])
        for rec in this_year_order:
            partner_id = rec['partner_id']

            partner_id_obj = self.env['res.partner'].browse(partner_id)
            rec_list = list(rec)
            rec_list[0] = partner_id_obj.name
            top_selling_customer.append({
                'customer': rec_list[0],
                'amount': rec['sum'],
            })
        return {
            'total_wishlist': len(wishlists),
            'total_order': len(orders),
            'new_order': len(new_order),
            'total_customer': len(customers),
            'time_range': 'this_week',
            'top_selling_customer': top_selling_customer,
        }

    def get_last_month(self):

        last_day_of_prev_month = date.today().replace(day=1) - timedelta(days=1)
        start_day_of_prev_month = date.today().replace(day=1) - timedelta(days=last_day_of_prev_month.day)

        self._cr.execute('''SELECT  partner_id, SUM(amount_total) FROM account_move WHERE is_from_mobile_order =True 
                 and state ='posted' and  date >=%s and date<= %s GROUP BY partner_id ORDER BY sum(amount_total) DESC limit 
                 10''', (start_day_of_prev_month, last_day_of_prev_month,))
        top_selling_customer = []
        # LAST MONTH ORDER
        this_year_order = self._cr.dictfetchall()
        orders = self.env['sale.order'].search(
            [('is_from_mobile_order', '=', True), ('state', '=', 'sale'), ('date_order', '<=', last_day_of_prev_month),
             ('date_order', '>=', start_day_of_prev_month)])
        # LAST MONTH NEW ORDER
        new_order_list = ['draft', 'sent']
        new_orders = self.env['sale.order'].search(
            [('is_from_mobile_order', '=', True), ('date_order', '<=', last_day_of_prev_month),
             ('date_order', '>=', start_day_of_prev_month)])
        new_order = new_orders.filtered(lambda b: b.state in new_order_list)

        # LAST MONTH NEW CUSTOMER
        customer_domain = [('is_from_mobile', '=', True), ('create_date', '<=', last_day_of_prev_month),
                           ('create_date', '>=', start_day_of_prev_month)]
        customers = self.env['res.partner'].search(customer_domain)

        wishlists = self.env['jr.wishlist'].search(
            [('date', '<=', last_day_of_prev_month), ('date', '>=', start_day_of_prev_month)])
        for rec in this_year_order:
            partner_id = rec['partner_id']

            partner_id_obj = self.env['res.partner'].browse(partner_id)
            rec_list = list(rec)
            rec_list[0] = partner_id_obj.name
            top_selling_customer.append({
                'customer': rec_list[0],
                'amount': rec['sum'],
            })

        return {
            'total_wishlist': len(wishlists),
            'total_order': len(orders),
            'new_order': len(new_order),
            'total_customer': len(customers),
            'time_range': 'last_month',
            'top_selling_customer': top_selling_customer,
        }
