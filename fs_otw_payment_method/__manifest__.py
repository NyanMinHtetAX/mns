# -*- coding: utf-8 -*-
{
    'name': 'OTW Payment Method',
    'version': '1.2',
    'summary': 'OTW Payment Method',
    'sequence': 100,
    'category': 'Accounting',
    'website': 'https://www.asiamatrixsoftware.com',
    'depends': ['account','stock'],
    'data': [
        'security/ir.model.access.csv',
        'views/otw_payment_method_views.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'LGPL-3',
}
