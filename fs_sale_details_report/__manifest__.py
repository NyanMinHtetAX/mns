# -*- coding: utf-8 -*-
{
    'name': 'Sale Details Report',
    'version': '15.0.1.0',
    'summary': 'Sale details report for field sale.',
    'sequence': 100,
    'category': 'Sale',
    'website': 'https://www.asiamatrixsoftware.com',
    'depends': [
        'daily_sale_summary',
        'report_xlsx',
        'report_py3o',
    ],
    'data': [
        'reports/sale_details_report.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'fs_sale_details_report/static/src/css/styles.css',
            'fs_sale_details_report/static/src/js/SaleDetailsReport.js',
        ],
        'web.assets_qweb': [
            'fs_sale_details_report/static/src/xml/*',
        ],
    },
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'LGPL-3',
}
