# -*- coding: utf-8 -*-
{
    'name': "User Access Right",

    'summary': """Access Right Module""",

    'description': """
        This Module Add user access right.
    """,

    'author': "Asia Matrix Software Solution",

    'website': "http://www.asiamatrixsoftware.com",

    'category': 'Security',

    'version': '1.9',

    'license': "LGPL-3",

    'depends': [
        'purchase',
        'multi_uom',
        'sale_extend',
        'stock',
    ],

    'data': [
        'security/purchase_access_views.xml',
        'security/account_access_views.xml',
        'security/base_security_extend.xml',
        'security/product_access_views.xml',
        'security/contact_access_views.xml',
        'security/access_right.xml',
        'view/purchase_views.xml',
        'view/product_views.xml',
        'view/sale_views.xml',
        'view/account_move_views.xml',
        'view/contact_views.xml',
        'view/return_btn_views.xml',
    ],

    'images': ['static/description/icon.png'],
}
