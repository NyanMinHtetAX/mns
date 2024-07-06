# -*- coding: utf-8 -*-
{
    'name': "purchase_pricelist_history",
    'summary': """
        Purchase Product Pricelist Record""",
    'description': """
        Record of purchase product based on different pricelist
    """,
    'author': "tinhtooaung",
    'website': "http://www.asiamatrixsoftware.com",
    'category': 'Purchase',
    'version': '1.7',
    'license': 'OPL-1',
    'depends': ['purchase'],
    'data': [
        'security/ir.model.access.csv',
        'views/pricelist_record_view.xml',
        'views/purchase_order_view.xml',

	
    ],
	'images'           : ['static/description/icon.png'],
}