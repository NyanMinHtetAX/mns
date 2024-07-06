# -*- coding: utf-8 -*-
{
    'name': 'Daily Sale Summary',
    'version': '3.3',
    'summary': 'Daily Sale Summary',
    'sequence': 100,
    'category': 'sale',
    'website': 'https://www.asiamatrixsoftware.com',
    'depends': [
        'fs_route_plan',
        'sales_team',
        'fs_payment_method',
        'sale_purchase_discount',
        'fs_sale_promotion',
    ],
    'data': [
        'data/ir_sequence.xml',
        'security/ir.model.access.csv',
        'views/daily_sale_summary_views.xml',
        'views/van_order_views.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'LGPL-3',
}
