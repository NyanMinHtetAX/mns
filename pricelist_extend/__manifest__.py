# -*- coding: utf-8 -*-
{
    "name": "Price-list Extend",
    "category": "Price-list Extend",
    "version": "1.1.5",
    "author": "Asia Matrix",
    "website": "https://asiamatrixsoftware.com",
    "description": 'Price-list Extend.',
    "depends": [
        'sale',
        'sale_stock','stock',
        'multi_uom',
    ],
    "data": [
        'views/res_partner_views.xml',
        'views/price_list_view.xml',
    ],
    "application": True,
    "installable": True,
    "auto_install": False,
    "license": "LGPL-3",
}
