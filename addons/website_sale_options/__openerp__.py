# -*- coding: utf-8 -*-
{
    'name': 'eCommerce Optional Products',
    'category': 'Website',
    'version': '1.0',
    'website': 'https://www.odoo.com/page/e-commerce',
    'description': """
Odoo E-Commerce
==================

        """,
    'author': 'Odoo SA',
    'depends': ['website_sale'],
    'data': [
        'views/product_template_views.xml',
        'views/templates.xml',
    ],
    'demo': [
        'data/product_demo.xml',
    ],
    'qweb': ['static/src/xml/*.xml'],
    'installable': True,
}
