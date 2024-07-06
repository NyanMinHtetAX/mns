# -*- coding: utf-8 -*-
{
    'name': "Stock Scrap Extend",

    'summary': """Stock Scrap""",

    'description': """
        Scrap Orders.
    """,

    'author': "Asia Matrix Software Solution",

    'website': "http://www.asiamatrixsoftware.com",

    'category': 'Stock',

    'version': '1.4',

    'license': "LGPL-3",

    'depends': [
        'stock',
        'stock_adjustment_backdate',
        'stock_account',
    ],
    'data': [
        'security/inventory_access_view.xml',
        'views/inventory_report_view.xml',
        'views/stock_scrap_view.xml',
        'views/backdate_adjustment_view.xml',
        'views/stock_quant_extend_view.xml',
    ],

    'installable': True,

    'application': False,
}