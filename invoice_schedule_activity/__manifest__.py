# -*- coding: utf-8 -*-
{
    'name': 'INV Due Date Schduler',

    'version': '1.0',

    'summary': 'For Invoice Due Date Scheduler',

    'description': """
      * For Invoice Due Date Scheduler.
    """,

    'category': 'Invoice',

    'Author': 'Asia Matrix Co.,Ltd',

    'website': "www.asiamatrixsoftware.com",

    'email': 'info@asiamatrixsoftware.com',

    'license': "LGPL-3",

    'depends': [
        'account',
        'mail'
    ],

    'data': [
        'data/invoice_scheduler.xml',
    ],

    'installable': True,

    'application': False,

    'auto_install': False,
}
