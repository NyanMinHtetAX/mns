# -*- coding: utf-8 -*-
{
    'name': 'Purchase Extend',
    'version': '2.9',
    'summary': 'Extension of Purchase module.',
    'category': 'Purchase',
    'website': "www.asiamatrixsoftware.com",
    'email': 'info@asiamatrixsoftware.com',
    'license': "LGPL-3",
    'depends': [
        'purchase',
        'product_extension',
        'multi_uom',
        'account',
        'hr'
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/purchase_order_view.xml',
        'views/account_move_views.xml',
        'views/res_partner_extend_views.xml',
        'views/account_payment_register_extend_views.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}
