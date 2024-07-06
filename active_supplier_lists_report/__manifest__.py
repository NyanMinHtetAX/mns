# -*- coding: utf-8 -*-
{
    'name': 'PO Active Supplier Lists Report',
    'version': '1.3',
    'summary': 'Active Supplier Lists Report From PO.',
    'category': 'Purchase',
    'website': "www.asiamatrixsoftware.com",
    'email': 'info@asiamatrixsoftware.com',
    'author': "Asia Matrix, MPP",
    'license': "LGPL-3",
    'depends': [
        'purchase',
        'purchase_extend',
    ],
    'data': [
        'security/ir.model.access.csv',
        'security/report_access.xml',
        'reports/po_supplier_lists_report_view.xml',
    ],
    'images': ['static/description/icon.png'],
    'installable': True,
    'application': False,
    'auto_install': False,
}
