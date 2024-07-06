# -*- coding: utf-8 -*-
{
    'name': 'Field Sale Payment Method',
    'version': '1.3',
    'summary': 'Field Sale Payment Method',
    'sequence': 100,
    'category': 'Accounting',
    'website': 'https://www.asiamatrixsoftware.com',
    'depends': ['account','base_field_sale'],
    'data': [
        'security/ir.model.access.csv',
        'views/fs_payment_method_views.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'LGPL-3',
}
