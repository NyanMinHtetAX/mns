
# -*- coding: utf-8 -*-
{
    'name': 'Delivery Report',
    'version': '1.1',
    'summary': 'Delivery Report.',
    'sequence': 100,
    'category': 'Sale',
    'website': 'https://www.asiamatrixsoftware.com',
    'depends': [
        'base',
        'account',
        'stock',
        'base_delivery_man'
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/delivery_report_views.xml'
    ],
    'assets': {

    },
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'LGPL-3',
}
