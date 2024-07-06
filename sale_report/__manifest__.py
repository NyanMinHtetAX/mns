# -*- coding: utf-8 -*-
{
    'name': 'Sale Report',
    'version': '1.5',
    'summary': 'Sale',
    'sequence': 100,
    'category': 'Sale',
    'author': 'Asia Matrix',
    'website': 'https://www.asiamatrixsoftware.com',
    'depends': [
        'sale',
        'multi_uom',
        'sale_purchase_discount'
    ],
    'data': [
        'security/ir.model.access.csv',
        'security/sale_report_access.xml',
        'reports/sale_reports_views.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}
