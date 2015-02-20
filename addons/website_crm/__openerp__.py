# -*- coding: utf-8 -*-
{
    'name': 'Contact Form',
    'category': 'Website',
    'website': 'https://www.odoo.com/page/website-builder',
    'summary': 'Create Leads From Contact Form',
    'version': '1.0',
    'description': """
Odoo Contact Form
====================

        """,
    'author': 'Odoo S.A.',
    'depends': ['website_partner', 'crm'],
    'data': [
        'data/website_crm_data.xml',
        'views/website_crm_templates.xml',
    ],
    'installable': True,
}
