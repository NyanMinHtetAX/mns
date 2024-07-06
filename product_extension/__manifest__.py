# -*- coding: utf-8 -*-
{
    'name': "Product IF Code",

    'summary': """Internal Reference Code""",

    'description': """
        1.Product Internal Reference Code
    """,

    'author': "Blue Stone Solution",
    'website': "http://www.blue-stone.net",


    'category': 'Inventory',
    'version': '1.6',
    'license': "LGPL-3",


    'depends': [
        'ax_base_setup',
        'stock',
        'product',

    ],

    'data': [
        'security/ir.model.access.csv',
        'datas/code_id_ir_sequence_data.xml',
        'views/product_product_views.xml',
        'views/product_brand_form_views.xml',
        'wizard/internal_reference_code.xml',
    ],

}
