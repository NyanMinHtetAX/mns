# -*- coding: utf-8 -*-
{
    'name': 'Fix Stock Valuation',
    'summary': 'To fix stock valuations and regenerate stock journals.',
    'author': "Asia Matrix Software Solution",
    'website': "http://www.asiamatrixsoftware.com",
    'category': 'Stock',
    'version': '1.7',
    'depends': [
        'stock_account',
    ],
    'data': [
        'security/ir.model.access.csv',
        'security/res_groups.xml',
        'views/stock_views.xml',
    ],
    'license': "LGPL-3",
}
