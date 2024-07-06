# -*- coding: utf-8 -*-
{
    'name': "sale_pricelist_history",
    'summary': """
        Sale Product Pricelist Record""",
    'description': """
        Record of sale product based on different pricelist
    """,
    'author': "Asia Matrix",
    'website': "http://www.asiamatrixsoftware.com",
    'category': 'Purchase',
    'version': '1.0',
    'license': 'OPL-1',
    'depends': ['sale'],
    'data': [
        'security/ir.model.access.csv',
        'view/product_template_form_view.xml',
        'view/sale_order_form_view.xml',
        'view/sale_pricelist_record.xml',

    ],
    'images': [],
}