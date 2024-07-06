# -*- coding: utf-8 -*-
{
    'name': 'Print Date All PDF',
    'version': '1.3',
    'summary': 'Place a sign on all PDF',
    'sequence': 100,
    'category': 'Reporting',
    'website': 'https://www.asiamatrixsoftware.com',
    'depends': [
        'base',
        'web',
        'account',
        'account_reports'
    ],
    'data': [
        'views/templates.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': True,
    'license': 'LGPL-3',
}
