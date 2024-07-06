# -*- coding: utf-8 -*-
{
    'name': 'Sale Team Extend',
    'version': '3.1',
    'summary': 'Sale Team management',
    'sequence': 100,
    'category': 'crm',
    'author': 'Asia Matrix',
    'website': 'https://www.asiamatrixsoftware.com',
    'depends': [
        'sales_team',
        'base_field_sale',
        'fleet',
        'fs_route_plan',
        'stock',
        'fs_payment_method',
        'product_extension',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/crm_team_view.xml',
        'views/sale_team_extend_view.xml',
        'views/product_views.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}
