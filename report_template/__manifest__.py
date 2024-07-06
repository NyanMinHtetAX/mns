# -*- coding: utf-8 -*-
# Part of Softhealer Technologies.

{
    "name": "Report Template",
    "version": "1.4",
    'website': "www.asiamatrixsoftware.com",
    'email': 'info@asiamatrixsoftware.com',
    'author': 'AsiaMatrix, MPP',
    "depends": ["account", 'sale', 'purchase', 'stock'],
    "data": [
        'security/ir.model.access.csv',
        'views/custom_report_template.xml',
        'views/purchase_order.xml',
        'views/sale_order.xml',
        'views/account_move.xml',
        'views/stock_move_views.xml',
    ],
    'license': "LGPL-3",
    'installable': True,
    'application': False,
    'auto_install': False,
}
