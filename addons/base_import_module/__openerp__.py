# -*- coding: utf-8 -*-
{
    'name': 'Base import module',
    'description': """
Import a custom data module
===========================

This module allows authorized users to import a custom data module (.xml files and static assests)
for customization purpose.
""",
    'category': 'Uncategorized',
    'website': 'https://www.odoo.com',
    'author': 'Odoo S.A.',
    'depends': ['web'],
    'installable': True,
    'auto_install': False,
    'data': ['views/base_import_module_view.xml'],
    'qweb': [],
    'test': [],
}
