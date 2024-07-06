{
    'name': 'POS Multi UOM',
    'category': 'Point of Sale',
    'author': 'Asia Matrix',
    'version': '15.0.2.2',
    'depends': [
        'point_of_sale',
        'multi_uom',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/pos_order_views.xml',
    ],
    'assets': {
        'point_of_sale.assets': [
            'multi_uom_pos_extend/static/src/css/*',
            'multi_uom_pos_extend/static/src/js/*',
        ],
        'web.assets_qweb': [
            'multi_uom_pos_extend/static/src/xml/*',
        ],
    },
    'installable': True,
    'license': 'LGPL-3',
}
