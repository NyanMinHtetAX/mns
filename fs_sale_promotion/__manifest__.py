# -*- coding: utf-8 -*-
{
    'name': 'Promotion Program',
    'version': '2.2',
    'category': 'Sales Promotion',
    'sequence': 1000,
    'author': 'Asia Matrix',
    'website': 'https://www.asiamatrixsoftware.com',
    'depends': [
        'sale_stock',
        'stock_account',
        'base_field_sale',
        'multi_uom',
        'ax_base_setup',
        'sale_team_extend',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/promotion_program_views.xml',
        'views/sale_order_views.xml',
        'views/crm_team_views.xml',
    ],
    'application': True,
    'license': 'LGPL-3',
}
