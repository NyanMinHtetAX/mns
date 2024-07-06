{
    'name': 'Stock Age SQL VIEW REPORT',
    'version': '2.3',
    'category': 'Report',
    'author': 'Asiamatrix',
    'website': 'https://asiamatrix.software.com',
    'license': 'LGPL-3',
    'depends': [
        'base', 
        'product',
        'account',
        'stock',
        'multi_uom'
    ],
    'data': [
        'security/ir.model.access.csv',
        'security/stock_age_report_access.xml',
        'views/stock_age_report.xml',
    ],
    'application': False,
    'installable': True,
    'auto_install': False,
}
