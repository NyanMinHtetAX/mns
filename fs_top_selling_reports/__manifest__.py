# -*- coding: utf-8 -*-
{
    'name': 'Top Selling Reports',
    'version': '15.0.1.0',
    'summary': 'Top Selling  Reports by Sales Team, Salesman, Product, Product Category, Customer.',
    'sequence': 100,
    'category': 'Sale',
    'website': 'https://www.asiamatrixsoftware.com',
    'depends': [
        'daily_sale_summary',
        'report_xlsx',
    ],
    'data': [
        'reports/top_selling_reports_views.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'fs_top_selling_reports/static/src/css/styles.css',
            'fs_top_selling_reports/static/src/js/TopSellingReport.js',
        ],
        'web.assets_qweb': [
            'fs_top_selling_reports/static/src/xml/*',
        ],
    },
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'LGPL-3',
}
