# -*- coding: utf-8 -*-
# Part of Kiran Infosoft. See LICENSE file for full copyright and licensing details.

{
    "name": "Product Movement Report",
    'version': '1.2',
    "author": "Asiamatrix",
    "website": "http://www.asiamatrixsoftware.com",
    "category": "stock",
    "depends": [
        "stock",
        "point_of_sale",
        "report_xlsx"
    ],
    'license': 'Other proprietary',
    "data": [
        "security/ir.model.access.csv",
        "wizard/product_report_wizard_view.xml"
    ],
    "installable": True,
    "application": False,   
}