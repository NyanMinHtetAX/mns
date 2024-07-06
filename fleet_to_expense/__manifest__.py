# -*- coding: utf-8 -*-
{
    'name': 'Fleet Extend',
    'version': '1.2',
    'summary': 'Extension of Fleet module carry fleet service cost to expense form',
    'category': 'Fleet',
    'website': "www.asiamatrixsoftware.com",
    'email': 'info@asiamatrixsoftware.com',
    'license': "LGPL-3",
    'depends': [
        'fleet','hr_expense',
    ],
    'data': [
        'views/fleet_service_form_view.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}
