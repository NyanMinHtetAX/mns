# -*- coding: utf-8 -*-
{
    'name': 'Expired Lots',
    'version': '15.0.1.1',
    'summary': 'Expired lots in inventory dashboard.',
    'sequence': 100,
    'category': 'Inventory',
    'website': 'https://www.asiamatrixsoftware.com',
    'depends': [
        'stock',
    ],
    'data': [
        'views/stock_views.xml',
        'views/res_config_settings_views.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'expired_lots/static/src/css/styles.css',
            'expired_lots/static/src/js/ExpiredLotsDashboardView.js',
            'expired_lots/static/src/js/ExpiredLotsDashboardRenderer.js',
        ],
        'web.assets_qweb': [
            'expired_lots/static/src/xml/*',
        ],
    },
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'LGPL-3',
}
