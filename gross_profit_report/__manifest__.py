
{
    'name': 'Gross Profit SQL VIEW REPORT',
    'version': '1.5',
    'category': 'Report',
    'author': 'Asiamatrix',
    'website': 'https://asiamatrix.software.com',
    'license': 'LGPL-3',
    'summary': 'View Gross Profit of last sale price and last purchase price.',
    'depends': [
        'base', 
        'sale',
        'product', 
        'multi_uom',
        'account'
    ],
    'data': [
        'security/ir.model.access.csv',
        'security/gross_profit_multi_company.xml',
        'reports/gross_profit_report_views.xml',
    ],
    'application': False,
    'installable': True,
    'auto_install': False,
}
