# -*- coding: utf-8 -*-
{
    'name': 'Customer Visit Report',
    'version': '0.8',
    'category': 'Field Sale',
    'sequence': 1000,
    'author': 'Asia Matrix',
    'website': 'https://www.asiamatrixsoftware.com',
    'depends': [
        'base_field_sale',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/customer_visit_report_view.xml',
        'views/visit_report_images_view.xml',
        'views/visit_attendance_views.xml',
        'wizards/visit_report_map_views.xml',
        'views/menuitems.xml',
    ],
    'application': True,
    'license': 'LGPL-3',
    'assets': {
        'web.assets_backend': [
            'fs_visit_report/static/src/css/styles.css',
            'fs_visit_report/static/src/css/mapbox.css',
            'fs_visit_report/static/src/js/visitmapWidget.js',
        ],
        'web.assets_qweb': [
            'fs_visit_report/static/src/xml/*',
        ],
    },
}
