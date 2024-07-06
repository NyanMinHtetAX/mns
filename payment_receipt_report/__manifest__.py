# -*- coding: utf-8 -*-
{
    'name': 'Payment Receipt PDF',
    'version': '1.0',
    'category': 'Show PDF Form',
    'author': 'Asia Matrix',
    'website': "https://www.asiamatrix.support/",
    'license': 'LGPL-3',
    'summary': """PDF For Payment Receipt""",
    'description': """
     For PDF Report.

    """,
    'depends': [
                'report_py3o',
                'account'
                ],
    'data': [
        'views/report_py3o.xml',
    ],
    'application': False,
    'installable': True,
    'auto_install': False,
}
