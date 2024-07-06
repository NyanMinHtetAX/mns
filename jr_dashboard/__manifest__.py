# -*- coding: utf-8 -*-
{
    'name': 'justOrder Dashboard',
    'version': '1.0',
    'summary': 'Just Order Detail Report',
    'sequence': 100,
    'category': 'Sale',
    'website': 'https://www.asiamatrixsoftware.com',
    'depends': [
        'base_just_order',
    ],
    'data': [
        'report/jr_detail_report.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'jr_dashboard/static/src/css/jr_db.css',
            'jr_dashboard/static/src/js/test_jr.js',
        ],
        'web.assets_qweb': [
            'jr_dashboard/static/src/xml/jr_detail_report_view.xml',
        ],
        'web.report_assets_pdf': [
        ],
    },
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'LGPL-3',
}
