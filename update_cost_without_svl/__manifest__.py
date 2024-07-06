{
    'name': 'Update Cost Without GL',
    'category': 'Accounting',
    'author': 'Asia Matrix',
    'version': '1.0',
    'depends': ['stock_account'],
    'data': [
        'security/ir.model.access.csv',
        'security/res_groups.xml',
        'views/res_config_settings_views.xml',
        'wizards/update_cost_without_svl_views.xml',
        'views/product_views.xml',
    ],
    'license': 'LGPL-3',
}
