# -*- coding: utf-8 -*-
{
    'name': 'Expense Approval Limit',
    'version': '1.1',
    'summary': 'Limited expense approve button by amount For Mya Ngwe San.',
    'description': """
       Limited amount by user who admin in expense.
        If this user limit expense amount, approve button will see in that limit or under.
    """,
    'category': 'Users, Expense',
    'author': 'Asia Matrix',
    'website': "www.asiamatrixsoftware.com",
    'email': 'info@asiamatrixsoftware.com',
    'license': "LGPL-3",
    'depends': [
        'base',
        'hr_expense',
    ],
    'data': [
        'views/res_users_views.xml',
        'views/hr_expense_sheet_views.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}
