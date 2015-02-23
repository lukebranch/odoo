# -*- coding: utf-8 -*-
{
    'name': 'Website Partner',
    'category': 'Website',
    'summary': 'Partner Module for Website',
    'version': '0.1',
    'description': """Base module holding website-related stuff for partner model""",
    'author': 'Odoo S.A.',
    'depends': ['website'],
    'data': [
        'views/res_partner_views.xml',
        'views/website_partner_templates.xml',
        'data/res_partner_data.xml',
    ],
    'demo': ['data/res_partner_demo.xml'],
    'qweb': [
    ],
    'installable': True,
}
