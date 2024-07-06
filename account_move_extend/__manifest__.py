# -*- coding: utf-8 -*-
{
    'name': 'Account Move Extend',

    'version': '1.1',
    'category': 'Account',
    'author': 'Asia Matrix, MPP',
    'website': "https://www.asiamatrix.support/",
    'license': 'LGPL-3',
    'summary': """Account Form""",
    'description': """
     For Account Move Remark

    """,
    'depends': [
        'account',
        'sale',
        'analytic_accounting',
    ],
    'data': [
        'views/account_move_views.xml',
    ],
    'application': False,
    'installable': True,
    'auto_install': False,
}
