# -*- coding: utf-8 -*-
{
    "name": "POS Extension",
    "category": "Point of Sale",
    "version": "1.1",
    "author": "Asia Matrix",
    "website": "https://asiamatrixsoftware.com",
    "description": 'Extension module for Point of Sale.',
    "depends": [
        'point_of_sale',
    ],
    "data": [
    ],
    'assets': {
        'web.assets_backend': [
            'pos_extend/static/src/js/ClientListScreen.js',
        ],
        'web.assets_qweb': [
            'pos_extend/static/src/xml/*',
        ],

    },
    "application": True,
    "installable": True,
    "auto_install": False,
    "license": "LGPL-3",
}
