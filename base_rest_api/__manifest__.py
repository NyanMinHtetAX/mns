# -*- coding: utf-8 -*-
{
  "name": "Base REST API",
  "category": "API",
  "version": "3.4",
  "author": "Asia Matrix",
  "website": "https://asiamatrixsoftware.com",
  "description": 'REST APIs.',
  "depends": [
    'web',
  ],
  "python": 'PyJWT',
  "data": [
    'security/ir.model.access.csv',
    'views/rest_api_views.xml',
    'views/templates.xml',
  ],
  "application": True,
  "installable": True,
  "auto_install": False,
  'license': 'LGPL-3',
}
