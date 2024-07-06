# -*- coding: utf-8 -*-
{
    'name': 'Delivery Man',
    'version': '3.7',
    'summary': 'To Hide Some Field in contact form',
    'description': """
       * To Hide Some Field in contact form. 
    """,
    'category': 'Contact',
    'website': "www.asiamatrixsoftware.com",
    'email': 'info@asiamatrixsoftware.com',
    'license': "LGPL-3",
    'depends': [
        'base',
        'sale',
        'purchase',
        'account_reports',
        'stock',
        'ax_base_setup',
        'fs_stock_request',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/res_partner_form_view.xml',
        'views/deliver_man_picking_view.xml',
        'views/delivery_man_menu.xml',
        'views/device_configuration_view.xml',
        'views/stock_picking_form_view.xml',
        'data/ir_sequence_data.xml',
        'wizard/delivery_assign_view.xml',
        'views/product_images_view.xml',
        'views/account_move_view.xml',
        'views/crm_extend_view.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'base_delivery_man/static/src/css/styles.css',
        ],
    },
    'installable': True,
    'application': False,
    'auto_install': False,
}
