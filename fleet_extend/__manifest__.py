# -*- coding: utf-8 -*-
{
    'name': 'Fleet Form Extend',
    'version': '1.0',
    'category': 'Contact Fleet',
    'author': 'Asia Matrix, MPP',
    'website': "https://www.asiamatrix.support/",
    'license': 'LGPL-3',
    'summary': """Fleet Form Contact""",
    'description': """
     For Driver & Future Driver in Fleet Form Contact.

    """,
    'depends': [
        'fleet',
        'sale_stock',
        'sale_extend',
    ],
    'data': [
        'views/res_partner_extend_views.xml',
    ],
    'application': False,
    'installable': True,
    'auto_install': False,
}
