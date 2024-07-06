{
    'name': 'POS Slip Design',
    'summary': """POS Receipt Design""",
    'version': '1.3.0',
    'description': """POS Receipt Design""",
    'author': 'Asia Matrix, MPP',
    'company': 'https://www.odoo.com',
    'website': 'www.asiamatrixsoftware.com',
    'category': 'Point of Sale',
    'depends': ['base', 'point_of_sale'],
    'license': 'LGPL-3',
    'data': [
        'views/pos_config_views.xml',
    ],
    'images': ['static/description/banner.png'],
    'assets': {
        'point_of_sale.assets': [
            'mns_pos_slip/static/src/js/*',
        ],
        'web.assets_qweb': [
            'mns_pos_slip/static/src/xml/pos_slip_extend.xml',
        ],
    },
    'demo': [],
    'installable': True,
    'application': True,
    'auto_install': False,

}
