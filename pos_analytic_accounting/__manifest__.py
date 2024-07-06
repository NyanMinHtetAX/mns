# -*- coding: utf-8 -*-
{
    "name": "POS Analytic Accounting",
    "category": "Accounting",
    "version": "1.2",
    "author": "Asia Matrix",
    "website": "https://asiamatrixsoftware.com",
    "description": 'Analytic account for Point of Sale.',
    "depends": [
        'point_of_sale',
        'analytic_accounting',
    ],
    "data": [
        'views/pos_views.xml',
    ],
    'assets': {
        'web.assets_backend': [
        ],
    },
    "application": True,
    "installable": True,
    "auto_install": False,
    "license": "LGPL-3",
}
