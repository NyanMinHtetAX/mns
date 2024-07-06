
{
    'name': 'Custom Product Labels',
    'version': '2.8',
    'category': 'Inventory',
    'author': 'Asiamatrix',
    'website': 'https://asiamatrix.software.com',
    'license': 'LGPL-3',
    'summary': 'Print custom product labels with barcode and for shelve tab',
    'images': ['static/description/banner.png'],
    'live_test_url': 'https://garazd.biz/r/1Jw',
    'depends': [
        'product', 'multi_uom','product_extension'
    ],
    'data': [
        'data/zero_precision.xml',
        'security/ir.model.access.csv',
        'report/barcode_report_kmart.xml',
        'report/product_label_reports.xml',
        'report/product_label_templates.xml',
        'wizard/print_product_label_views.xml',
        'report/product_label_template_shelvetab.xml',
        'views/product_form_view.xml',
    ],
    'demo': [
        'demo/product_demo.xml',
    ],
    'assets': {
        'web.report_assets_common': [
            'garazd_product_label/static/src/css/style.css',
        ],
        'web.report_assets_pdf': [
            'garazd_product_label/static/src/css/style.css',
        ]
    },
    'external_dependencies': {
    },
    'support': 'support@garazd.biz',
    'application': False,
    'installable': True,
    'auto_install': False,
}
