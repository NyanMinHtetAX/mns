# -*- coding: utf-8 -*-
{
    'name': 'Sale Consignment',
    'version': '15.0.1.0',
    'summary': 'Sale consignment with request forms.',
    'sequence': 100,
    'category': 'Sale',
    'website': 'https://www.asiamatrixsoftware.com',
    'depends': [
        'stock_account',
        'daily_sale_summary',
    ],
    'data': [
        'security/ir.model.access.csv',
        'data/ir_sequence.xml',
        'views/res_partner_views.xml',
        'views/consignment_views.xml',
        'views/res_config_settings_views.xml',
        'views/menuitems.xml',
    ],
    'assets': {
    },
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'LGPL-3',
}
