# -*- coding: utf-8 -*-
{
    'name': 'Stock Requisition',
    'version': '15.0.2.5',
    'summary': 'Stock requisition and stock return',
    'sequence': 100,
    'category': 'Inventory',
    'website': 'https://www.asiamatrixsoftware.com',
    'depends': ['stock', 'fleet', 'base_field_sale','base'],
    'data': [
        'data/ir_sequence.xml',
        'views/stock_requisition_views.xml',
        'views/stock_return_views.xml',
        'views/stock_van_transfer_views.xml',
        'views/stock_quant_views.xml',
        'views/res_users_views.xml',

    ],
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'LGPL-3',
}
