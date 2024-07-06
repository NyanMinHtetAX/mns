# -*- coding: utf-8 -*-
{
    'name': 'Purchase FOC',
    'version': '1.1',
    'category': 'Purchase',
    'sequence': 1000,
    'author': 'Asia Matrix',
    'website': 'https://www.asiamatrixsoftware.com',
    'depends': [
        'multi_uom',
        'purchase_stock',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/purchase_foc_views.xml',
    ],
    'application': True,
    'license': 'LGPL-3',
}
