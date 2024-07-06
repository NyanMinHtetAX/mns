# -*- coding: utf-8 -*-
{
    'name': 'Stock Quant Extend',
    'version': '1.0',
    'summary': 'To go to product form from stock quant',
    'description': """
       To go to product form from stock quant
    """,
    'category': 'stock',
    'website': "www.asiamatrixsoftware.com",
    'email': 'info@asiamatrixsoftware.com',
    'license': "LGPL-3",
    'depends': [
        'base',
        'stock',
        'stock_barcode',
    ],
    'data': [
        'views/stock_quant_views.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}
