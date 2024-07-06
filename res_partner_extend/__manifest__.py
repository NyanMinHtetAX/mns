# -*- coding: utf-8 -*-
{
    'name': 'Partner ',

    'version': '2.4',

    'summary': 'outlet and contact form repair',

    'description': """
       * Outlet and Res Partner Repair. 
    """,

    'category': 'Contact',

    'website': "www.asiamatrixsoftware.com",

    'email': 'info@asiamatrixsoftware.com',

    'license': "LGPL-3",

    'depends': [
        'base',
        'contacts',
        'mail',
        'sale',
        'sales_team',
        'ax_base_setup',
    ],

    'data': [

        'security/ir.model.access.csv',
        'views/res_partner_outlet_view.xml',
        'views/res_partner_view.xml',
        'views/sale_team_view.xml',
        'views/sale_channel_views.xml',
        'views/res_company_form_view.xml',

    ],

    'installable': True,

    'application': False,

    'auto_install': False,
}
