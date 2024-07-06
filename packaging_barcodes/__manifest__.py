# -*- coding: utf-8 -*-
{
    "name": "Product Packaging Barcode",
    "category": "Point of Sale",
    "version": "1.0",
    "author": "Asia Matrix",
    "website": "https://asiamatrixsoftware.com",
    "description": 'Make Packagings Barcode scannable.',
    "depends": [
        'product',
        'multi_uom',
        'multi_uom_pos_extend',
        'sale'
    ],
    "data": [
        'views/product_packaging_view.xml',
        'views/product_product_view.xml'
    ],
    'assets': {
        'web.assets_backend': [
            'packaging_barcodes/static/src/js/models.js',
            'packaging_barcodes/static/src/js/db.js',
            'packaging_barcodes/static/src/js/ProductWidgetControlPanel.js'

        ],
    },
    "application": True,
    "installable": True,
    "auto_install": False,
    "license": "LGPL-3",
}
