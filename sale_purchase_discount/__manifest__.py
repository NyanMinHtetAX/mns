# -*- coding: utf-8 -*-
{
    'name': 'Discount',
    'version': '15.0.1.3',
    'summary': 'Discount in sale in purchase',
    'description': """
       Both percentage discount and fixed discount as well as global discount in
        Sales, Purchase and Accounting.
    """,
    'category': 'Discount',
    'website': "www.asiamatrixsoftware.com",
    'email': 'info@asiamatrixsoftware.com',
    'license': "LGPL-3",
    'depends': [
        'sale',
        'purchase',
        'stock_account',
    ],
    'data': [
        'views/sale_order_views.xml',
        'views/purchase_order_views.xml',
        'views/account_move_views.xml',
        'views/res_config_settings_views.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'sale_purchase_discount/static/src/css/styles.css',
        ],
    },
    'installable': True,
    'application': False,
    'auto_install': False,
}
