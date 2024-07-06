# -*- coding: utf-8 -*-
{
    'name': "Dynamic Access Rights",
    'summary': """Hide Buttons and Pages, add and remove users to and from Groups in Batch""",
    'description': """
       This module makes configuring access rights in odoo easy. 
       You can hide buttons and pages/tabs from a set of  users or groups. 
       Also it helps you to easily add users to the right groups and remove
        them from other groups""",
    'version': '15.0.1.1.0',
    'category': 'Human Resources',
    'sequence': 100,
    'depends': ['base', 'mail', 'web_domain_field'],
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'views/views.xml',
        'wizard/message_wizard.xml',
        'data/data.xml'
    ],
    'assets': {
        'web.assets_backend': [
            'htsk_dynamic_access_rights/static/src/js/crawler.js',
            'htsk_dynamic_access_rights/static/src/css/crawler.scss'
        ],
    },
    'application': True,
    'installable': True,
    'auto_install': False,

    'author': "Hyperthink Systems Kenya",
    'website': 'https://hyperthinkkenya.co.ke',
    'license': 'AGPL-3',
    'price': '250.0',
    'currency': 'USD',
    'images': ['static/description/banner.gif']
}
