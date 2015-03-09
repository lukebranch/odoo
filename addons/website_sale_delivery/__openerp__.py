# -*- coding: utf-8 -*-
{
    'name': 'eCommerce Delivery',
    'category': 'Website',
    'summary': 'Add Delivery Costs to Online Sales',
    'website': 'https://www.odoo.com/page/e-commerce',
    'version': '1.0',
    'description': """
Delivery Costs
==============
""",
    'author': 'Odoo SA',
    'depends': ['website_sale', 'delivery'],
    'data': [
        'views/website_sale_delivery.xml',
        'views/website_sale_delivery_view.xml',
        'security/ir.model.access.csv',
    ],
    'installable': True,
}
