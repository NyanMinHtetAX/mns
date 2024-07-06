# -*- coding: utf-8 -*-
{
    'name': 'OneSignal Notification ',
    'version': '2.2',
    'summary': 'Onesignal notification to send to respective partners.',
    'category': 'Contact',
    'website': "www.asiamatrixsoftware.com",
    'email': 'info@asiamatrixsoftware.com',
    'license': "LGPL-3",
    'depends': [
        'base_setup',
        'fs_stock_request',
        'fs_route_plan'
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/mobile_device_views.xml',
        'views/route_plan_views.xml',
        'views/pricelist_views.xml',
        'views/res_config_settings_views.xml',
        'views/res_partner_views.xml',
        'wizards/notify_views.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}
