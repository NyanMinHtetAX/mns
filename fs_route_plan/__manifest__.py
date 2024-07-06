# -*- coding: utf-8 -*-
{
    'name': 'Route Plan',
    'version': '2.7.1',
    'category': 'Field Sale',
    'sequence': 1000,
    'author': 'Asia Matrix',
    'website': 'https://www.asiamatrixsoftware.com',
    'depends': [
        'ax_base_setup',
        'res_partner_extend',
    ],
    'data': [
        'data/week_data.xml',
        'security/ir.model.access.csv',
        'wizards/assign_sales_teams_views.xml',
        'wizards/select_partner_wizard_view.xml',
        'views/route_plan_views.xml',
        'views/menuitems.xml',
    ],
    'application': True,
    'license': 'LGPL-3',
    'assets': {
        'web.assets_backend': [
            'fs_route_plan/static/src/css/styles.css',
            'fs_route_plan/static/src/js/mapWidget.js',
            'fs_route_plan/static/src/js/mapRenderer.js',
            'fs_route_plan/static/src/js/RoutePlan.js',
        ],
        'web.assets_qweb': [
            'fs_route_plan/static/src/xml/*',
        ],
    },
}
