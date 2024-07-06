# -*- coding: utf-8 -*-
{
    'name': 'Field Sale Multi Company',
    'version': '15.0.1.1',
    'summary': 'Multi Company environment in field sale related records.',
    'sequence': 100,
    'category': 'Multi Company',
    'website': 'https://www.asiamatrixsoftware.com',
    'depends': [
        'daily_sale_summary',
        'fs_route_plan',
        'fs_visit_report',
        'fs_payment_collection',
        'fs_sale_promotion',
        'stock_multi_scrap',
    ],
    'data': [
        'security/ir_rules.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'LGPL-3',
}
