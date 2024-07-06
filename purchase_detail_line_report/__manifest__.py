# -*- coding: utf-8 -*-
{
    'name': 'Purchase Details Line Report',
    'version': '2.3',
    'summary': 'Purchase details line report.',
    'category': 'Purchase',
    'website': "www.asiamatrixsoftware.com",
    'email': 'info@asiamatrixsoftware.com',
    'license': "LGPL-3",
    'depends': [
        'purchase_stock',
        'multi_uom',
        'sale_purchase_discount',
        'purchase'
    ],
    'data': [
        'security/ir.model.access.csv',
        'security/report_access.xml',
        'reports/purchase_reports_views.xml',
        'views/purchase_order_view.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}
