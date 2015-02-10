# -*- coding: utf-8 -*-

{
    'name': 'Team Page',
    'category': 'Website',
    'summary': 'Present Your Team',
    'version': '1.0',
    'description': """
Our Team Page
=============

        """,
    'author': 'Odoo S.A.',
    'depends': ['website', 'hr'],
    'demo': [
        'data/hr_employee_demo.xml'
    ],
    'data': [
        'data/website_hr_data.xml',
        'views/hr_employee_views.xml',
        'views/website_hr_templates.xml',
        'security/ir.model.access.csv',
        'security/hr_employee_security.xml'
    ],
    'installable': True
}
