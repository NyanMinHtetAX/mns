# -*- coding: utf-8 -*-
{
    'name': 'Daily Sale Summary Report',
    'version': '15.0.1.7',
    'summary': 'Daily sale summary report for field sale.',
    'sequence': 100,
    'category': 'Sale',
    'website': 'https://www.asiamatrixsoftware.com',
    'depends': [
        'daily_sale_summary',
        'fs_route_plan',
        'fs_visit_report',
        'fs_payment_collection',
        'report_py3o',
    ],
    'data': [
        'reports/daily_sale_report.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'fs_daily_sale_report/static/src/css/styles.css',
            'fs_daily_sale_report/static/src/js/DailySaleReport.js',
        ],
        'web.assets_qweb': [
            'fs_daily_sale_report/static/src/xml/*',
        ],
        'web.report_assets_pdf': [
            'fs_daily_sale_report/static/src/css/reportStyles.css',
        ],
    },
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'LGPL-3',
}
