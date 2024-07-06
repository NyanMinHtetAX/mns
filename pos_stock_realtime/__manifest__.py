# -*- coding: utf-8 -*-
{
    'name': 'POS Realtime Stock',
    'version': '1.1',
    'category': 'Point of Sale',
    'sequence': 10000,
    'author': 'Asia Matrix',
    'depends': ['point_of_sale'],
    'data': [
        'views/assets.xml',
        'views/pos_views.xml',
    ],
    'qweb': [
        'static/src/xml/ProductList.xml',
        'static/src/xml/ProductItem.xml',
    ],
    'application': True,
    'license': 'LGPL-3',
    'assets': {
        'web.assets_qweb': [
            'pos_stock_realtime/static/src/xml/*',
        ],
    },
}

