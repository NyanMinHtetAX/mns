# -*- coding: utf-8 -*-
{
    'name': "Lock Date Access For Sale, Purchase, Invoice, Inventory",

    'summary': """Lock Date Access""",

    'description': """""",

    'author': "Asia Matrix Software Solution, MPP",

    'website': "http://www.asiamatrixsoftware.com",

    'license': 'LGPL-3',

    'category': 'Sale',

    'version': '1.4',

    'depends': [
                'sale',
                'purchase_stock',
                'stock',
                'stock_landed_costs',
                ],

    'data': [
        'views/res_users_extend_views.xml',
    ],

    'installable': True,

    'application': False,
}