# -*- coding: utf-8 -*-
{
    "name": "Just Order",
    "category": "just_order",
    "version": "3.2",
    "author": "Asia Matrix",
    "website": "https://asiamatrixsoftware.com",
    "description": 'Just Order module',
    "depends": ['mail', 'product', 'sale', 'ax_base_setup','delivery' ],
    "data": [

        'views/just_order_order_view.xml',
        'views/product_view.xml',
        'views/category_view.xml',
        'views/report_view.xml',
        'wizards/app_key_view.xml',
        'views/jr_setting_view.xml',
        'views/jr_wishlist_view.xml',
        'views/partner_view.xml',
        'views/menuItems.xml',
        'security/ir.model.access.csv'
    ],
    "application": True,
    "installable": True,
    "auto_install": False,
    'license': 'LGPL-3',
}
