# -*- coding: utf-8 -*-
{
    'name': 'HR Gamification',
    'version': '1.0',
    'author': 'Odoo S.A.',
    'category': 'hidden',
    'website': 'https://www.odoo.com/page/employees',
    'depends': ['gamification', 'hr'],
    'description': """Use the HR ressources for the gamification process.

The HR officer can now manage challenges and badges.
This allow the user to send badges to employees instead of simple users.
Badge received are displayed on the user profile.
""",
    'data': [
        'security/ir.model.access.csv',
        'security/gamification_security.xml',
        'wizard/gamification_badge_user_wizard_views.xml',
        'views/gamification_views.xml',
        'views/hr_employee_views.xml',
        'views/gamification_templates.xml',
    ],
    'auto_install': True,
}
