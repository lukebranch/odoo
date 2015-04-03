# -*- coding: utf-8 -*-
{
    'name': 'Payment: Website Integration',
    'category': 'Website',
    'summary': 'Payment: Website Integration',
    'version': '1.0',
    'description': """Bridge module for acquirers and website.""",
    'author': 'Odoo SA',
    'depends': [
        'website',
        'payment',
    ],
    'data': [
        'views/website_payment_templates.xml',
        'views/website_views.xml',
    ],
}
