# -*- coding: utf-8 -*-
{
    'name': 'Inventory Report(Fieldsale)',
    'version': '15.0.1.7',
    'summary': 'Inventory report by sale team for field sales.',
    'sequence': 100,
    'category': 'Sale',
    'website': 'https://www.asiamatrixsoftware.com',
    'depends': [
        'daily_sale_summary',
        'report_py3o',
    ],
    'data': [
        'reports/fs_inventory_report_views.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'fs_inventory_report/static/src/css/styles.css',
            'fs_inventory_report/static/src/js/FsInventoryReport.js',
        ],
        'web.assets_qweb': [
            'fs_inventory_report/static/src/xml/*',
        ],
    },
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'LGPL-3',
}
