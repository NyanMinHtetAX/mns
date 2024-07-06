# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    'name': 'Dynamic PDF Report',
    'version': '2.7.2',
    'summary': 'Dynamic PDF Report.',
    'sequence': 10,
    'category': 'Sale & Purchase',
    'website': 'https://www.odoo.com',
    'depends' : ['sale', 'stock', 'account', 'purchase_stock', 'fs_purchase_foc', 'portal', 'web'],
    'data': [
        'reports/reports.xml',
        'views/purchase_order_views.xml',
        'views/account_move_views.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'LGPL-3',
}
