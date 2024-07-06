# -*- coding: utf-8 -*-
{
    'name': 'SO Active Customer Lists Report',
    'version': '1.3',
    'summary': 'Active Customer Lists Report From SO.',
    'category': 'Purchase',
    'website': "www.asiamatrixsoftware.com",
    'email': 'info@asiamatrixsoftware.com',
    'author': "Asia Matrix, MPP",
    'license': "LGPL-3",
    'depends': [
        'sale',
        'sale_extend',
    ],
    'data': [
        'security/ir.model.access.csv',
        'security/report_access.xml',
        'reports/so_customer_lists_report_view.xml',
    ],
    'images': ['static/description/icon.png'],
    'installable': True,
    'application': False,
    'auto_install': False,
}
