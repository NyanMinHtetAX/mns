# -*- coding: utf-8 -*-
{
    'name': 'All PDF Form',
    'version': '2.7',
    'category': 'Show PDF Form',
    'author': 'Asia Matrix',
    'website': "https://www.asiamatrix.support/",
    'license': 'LGPL-3',
    'summary': """All PDF""",
    'description': """
     For PDF Report.

    """,
    'depends': ['sale',
                'report_py3o',
                'stock',
                'account',
                'hr',
                'sale_extend',
                'purchase_extend',
                'report_myanmar_font',
                ],
    'data': [
        'views/report_py3o.xml',
        'views/stock_picking_extend_views.xml',
    ],
    'application': False,
    'installable': True,
    'auto_install': False,
}
