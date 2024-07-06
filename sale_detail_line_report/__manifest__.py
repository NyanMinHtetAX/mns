# -*- coding: utf-8 -*-
{
    'name': 'Sale Details Line Report',
    'version': '2.3',
    'summary': 'Sale details line report .',
    'category': 'Sale',
    'website': "www.asiamatrixsoftware.com",
    'email': 'info@asiamatrixsoftware.com',
    'license': "LGPL-3",
    'depends': [
        'sale_stock',
        'multi_uom'
    ],
    'data': [
        'views/sale_order_view.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}
