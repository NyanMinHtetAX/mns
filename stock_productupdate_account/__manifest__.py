# -*- coding: utf-8 -*-
{
    'name': 'Product Update Account',

    'version': '1.0',

    'category': 'Accounting',

    'sequence': 1001,

    'author': 'Asia Matrix',

    'depends': [
        'stock_account',
        'account',
    ],

    'data': [
        'views/product_category_views.xml',
    ],

    'application': True,

    'license': 'LGPL-3',
}
