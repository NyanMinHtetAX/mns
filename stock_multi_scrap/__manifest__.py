# -*- coding: utf-8 -*-
{
    'name': 'Multi Scrap',
    'version': '15.0.1.3',
    'license': 'LGPL-3',
    'summary': 'Multi Scrap Form',
    'description': """
       * Added menu multi scrap in inventory module. 
    """,
    'category': 'Stock',
    'website': "www.asiamatrixsoftware.com",
    'email': 'info@asiamatrixsoftware.com',
    'depends': [
        'stock',
        'base_field_sale',
        'multi_uom',
    ],
    'data': [
        'security/ir.model.access.csv',
        'data/ir_sequence.xml',
        'views/multi_scrap_views.xml',
        'wizards/stock_warn_insufficient_qty_views.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}
