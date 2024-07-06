{
    'name': 'Payment in Due Date SQL VIEW REPORT',
    'version': '1.2',
    'category': 'Report',
    'author': 'Asiamatrix',
    'website': 'https://asiamatrix.software.com',
    'license': 'LGPL-3',
    'depends': [
        'base', 
        'account',
        'sale'
    ],
    'data': [
        'security/ir.model.access.csv',
        'security/invoice_due_report_access.xml',
        'reports/invoice_due_date_report.xml',
        'views/account_payment_date.xml'
    ],
    'application': False,
    'installable': True,
    'auto_install': False,
}
