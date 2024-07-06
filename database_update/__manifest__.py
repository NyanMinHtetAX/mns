# -*- coding: utf-8 -*-
{
    'name': 'Update Database',
    'version': '1.1',
    'category': 'Database',
    'summary': 'Datase Update',
    'Description': """
        1. Valuation date update
        2. Journal date update
    """,
    'author': 'Asia Matrix',
    'depends': [
        'stock_account',
        'account',
    ],
    'data': [
        'security/stock_valuation_date_access.xml',
        'security/ir.model.access.csv',
        'wizard/valuation_update_views.xml',
        'wizard/account_update_views.xml',
    ],
    'application': True,
    'license': 'LGPL-3',
}
