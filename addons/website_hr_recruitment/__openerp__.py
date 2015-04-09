# -*- coding: utf-8 -*-

{
    'name': 'Online Jobs',
    'category': 'Website',
    'version': '1.0',
    'summary': 'Job Descriptions And Application Forms',
    'description': """
Odoo Contact Form
====================

        """,
    'author': 'Odoo S.A.',
    'depends': ['website_partner', 'hr_recruitment', 'website_mail'],
    'data': [
        'security/ir.model.access.csv',
        'security/hr_recruitment_security.xml',
        'data/website_hr_recruitment_data.xml',
        'views/hr_job_views.xml',
        'views/website_hr_recruitment_templates.xml'
    ],
    'demo': [
        'data/hr_job_demo.xml',
    ],
    'installable': True,
}
