# -*- coding: utf-8 -*-
{
    'name': 'Sale Stock Extend',
    'version': '1.3',
    'summary': 'Extension module of inventory & sale modules.',
    'category': 'Inventory',
    'website': "www.asiamatrixsoftware.com",
    'email': 'info@asiamatrixsoftware.com',
    'license': "LGPL-3",
    'depends': [
        'account',
        'sale_stock',
    ],
    'data': [
        'views/stock_views.xml',
        'views/sale_views.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}
