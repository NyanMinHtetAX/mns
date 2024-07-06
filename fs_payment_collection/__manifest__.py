# -*- coding: utf-8 -*-
{
    'name': 'Payment Collection',
    'version': '15.0.2.1',
    'summary': 'Payment collection',
    'sequence': 100,
    'category': 'Accounting',
    'website': 'https://www.asiamatrixsoftware.com',
    'depends': [
        'fs_payment_method',
        'daily_sale_summary',
        'account',
    ],
    'data': [
        'security/ir.model.access.csv',
        'data/ir_sequence.xml',
        'views/payment_collection_views.xml',
        'views/payment_collection_one_views.xml',
        'views/account_views.xml',
        'views/daily_sale_views.xml',
        'wizards/assign_to_cash_collector_views.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'LGPL-3',
}
