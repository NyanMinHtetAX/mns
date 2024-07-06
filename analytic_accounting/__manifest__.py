# -*- coding: utf-8 -*-
{
  "name": "Analytic Accounting",
  "category": "Accounting",
  "version": "1.9.1",
  "author": "Asia Matrix",
  "website": "https://asiamatrixsoftware.com",
  "description": 'Analytic account in all module.',
  "depends": [
    'sale_stock',
    'stock_account',
    'account_reports',
  ],
  "data": [
    'views/sale_order_views.xml',
    'views/stock_views.xml',
    'views/account_views.xml',
    'views/hr_expense_sheet_view.xml',
  ],
  # 'assets': {
  #   'web.assets_backend': [
  #     'analytic_accounting/static/src/js/account_reports.js',
  #   ],
  # },
  "application": True,
  "installable": True,
  "auto_install": False,
  "license": "LGPL-3",
}
