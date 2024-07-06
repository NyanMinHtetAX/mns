# -*- coding: utf-8 -*-
{
    'name': "Myanmar Font for QWeb PDF ",
    'summary': """""",
    'author': 'Asia Matrix',
    'version': '1.7',
    'depends': [
            'base',
        ],

    'assets': {
        'web.assets_frontend': [
            'report_myanmar_font/static/src/scss/fonts.scss',
        ],
        'web.assets_qweb': [
            'report_myanmar_font/static/src/scss/fonts.scss',
        ],
        'web.report_assets_common': [
            'report_myanmar_font/static/src/scss/fonts.scss',
        ],
    },
    'data': ['views/invoice_report.xml'],
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
    'external_dependencies': {
         'python': ['python-myanmar'],
     },
}
