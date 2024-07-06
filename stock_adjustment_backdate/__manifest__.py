# -*- coding: utf-8 -*-
{
    'name': 'Stock Adjustment Backdate',
    'version': '15.0.2.0',
    'summary': 'Stock adjustment with backdate',
    'sequence': 100,
    'description': """
        Stock adjustment with backdate feature.
        * V-15.0.2.0 Picking Validate Issue
    """,
    'category': 'Inventory',
    'website': 'https://www.asiamatrixsoftware.com',
    'depends': ['stock_account','stock_landed_costs', 'web'],
    'data': [
        'security/ir.model.access.csv',
        'security/menu_invisible_security.xml',
        'data/ir_sequence.xml',
        'views/user_view.xml',
        'views/stock_adjustment_views.xml',
        'views/stock_views.xml',
        'views/sale_views.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'LGPL-3',
    'assets': {
        'web.assets_backend': [
            'stock_adjustment_backdate/static/src/js/validate_btn_controller.js',
            'stock_adjustment_backdate/static/src/js/validate_btn_view.js',
        ],
        'web.assets_qweb': [
            'stock_adjustment_backdate/static/src/xml/*',
        ],
    },
}
