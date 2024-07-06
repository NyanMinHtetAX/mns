{
    'name': 'Multi UOM',
    'category': 'Inventory',
    'author': 'Asia Matrix',
    'version': '15.0.4.2',
    'depends': [
        'sale_stock',
        'purchase_stock',
        'purchase_requisition',
        'stock_account',
        'sale_purchase_discount',
        'sale_purchase_inter_company_rules',
        'ax_log_note_form'  # For Purchase UOM field of product
    ],
    'data': [
        'security/res_groups.xml',
        'security/ir.model.access.csv',
        'data/decimal_precision.xml',
        'views/product_views.xml',
        'views/sale_order_views.xml',
        'views/purchase_order_views.xml',
        'views/purchase_requisition_views.xml',
        'views/stock_views.xml',
        'views/account_move_views.xml',
        'views/res_config_settings_views.xml',
        'wizards/stock_picking_return.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'multi_uom/static/src/js/list.js',
            'multi_uom/static/src/css/list.css',
        ],
    },
    'installable': True,
    'license': 'LGPL-3',
}
