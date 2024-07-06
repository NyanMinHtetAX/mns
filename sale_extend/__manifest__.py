# -*- coding: utf-8 -*-
{
    'name': 'Sales Extend',
    'version': '2.8',
    'summary': 'Extension of sales module.',
    'category': 'Sales',
    'website': "www.asiamatrixsoftware.com",
    'email': 'info@asiamatrixsoftware.com',
    'license': "LGPL-3",
    'depends': [
        'sale_management',
        'sale_stock',
        'fleet',
        'mail'
    ],
    'data': [
        'security/ir.model.access.csv',
        'security/sale_price_change_access.xml',
        'views/sale_views.xml',
        'views/res_partner_view.xml',
        'views/partner_class_view.xml',
        'views/stock_picking_view.xml',
        'views/account_move_view.xml',
        'views/account_report_inherit_view.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}
