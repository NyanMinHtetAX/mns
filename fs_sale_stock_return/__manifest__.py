# -*- coding: utf-8 -*-
{
    'name': 'Sale Stock Return',
    'version': '15.0.1.9',
    'summary': 'Sale stock return',
    'sequence': 100,
    'category': 'Inventory',
    'website': 'https://www.asiamatrixsoftware.com',
    'depends': [
        'base_field_sale',
        'fs_route_plan',
        'daily_sale_summary',
        'sale_team_extend',
        'stock_account',
    ],
    'data': [
        'security/ir.model.access.csv',
        'data/ir_sequence.xml',
        'views/daily_sale_summary.xml',
        'views/sale_stock_return_views.xml',
        'wizards/sale_stock_return_image_views.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'LGPL-3',
}
