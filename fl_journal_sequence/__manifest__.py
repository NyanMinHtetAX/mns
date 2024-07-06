# -*- coding: utf-8 -*-
{
    'name': 'Journal Sequence',
    'version': '15.0.1.0.0',
    'category': 'Accounting/Accounting',
    'summary': 'Option to add sequence configuration for journal sequence and refund journal sequence, Journal Entry Sequence for Invoice, Journal Sequence For Odoo 14',
    'description': """
        This module allows an option to add sequence configuration for journal sequence and refund journal sequence,
        User can easily configure and change the invoice/bill sequence number from the journals,
        Allowed to create and modify journal sequence,
        Allowed to create and modify refund journal sequence.
    """,
    'sequence': 1,
    'author': 'Futurelens',
    'website': 'http://thefuturelens.com',
    'depends': ['account'],
    'data': [
        'views/account_journal_views.xml',
    ],
    'qweb': [],
    'css': [],
    'js': [],
    'images': [
        'static/description/banner_journal_sequence.png',
    ],
    'demo': [],
    'installable': True,
    'auto_install': False,
    'application': True,
    'license': 'OPL-1',
    'price': 10,
    'currency': 'EUR',
    'live_test_url': 'https://youtu.be/--ONhNZCbpc',
}
