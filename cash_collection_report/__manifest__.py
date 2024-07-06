
# -*- coding: utf-8 -*-
{
    'name': 'Cash Collection Report',
    'version': '1.1',
    'summary': 'Cash Collection Report.',
    'sequence': 100,
    'category': 'Sale',
    'website': 'https://www.asiamatrixsoftware.com',
    'depends': [
        'base',
        'account',
        'fs_payment_collection',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/cash_collection_views.xml'
    ],
    'assets': {

    },
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'LGPL-3',
}
