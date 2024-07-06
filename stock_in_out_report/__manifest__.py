# -*- coding: utf-8 -*-
{
    'name': 'Stock In/Out Report',
    'version': '1.1',
    'summary': 'Stock In/Out Report for inventory',
    'sequence': 101,
    'category': 'Inventory',
    'website': 'https://www.asiamatrixsoftware.com',
    'author': 'Asia Matrix, MPP',
    'depends': [
        'sale_stock',
        'purchase_stock',
        'stock_backdate_report',
        'report_xlsx',
    ],
    'data': [
        'security/ir.model.access.csv',
        'wizards/stock_in_out_wizard_views.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'LGPL-3',
}
