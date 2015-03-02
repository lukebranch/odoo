# -*- coding: utf-8 -*-
{
    'name': 'Google Drive™ integration',
    'version': '0.2',
    'author': 'Odoo SA',
    'website': 'https://www.odoo.com',
    'category': 'Tools',
    'installable': True,
    'auto_install': False,
    'data': [
        'security/ir.model.access.csv',
        'views/res_config_user_view.xml',
        'data/google_drive_data.xml',
        'views/google_drive.xml',
    ],
    'demo': [
        'demo/google_drive_demo.xml'
    ],
    'depends': ['base_setup', 'google_account'],
    'description': """
Integrate google document to OpenERP record.
============================================

This module allows you to integrate google documents to any of your OpenERP record quickly and easily using OAuth 2.0 for Installed Applications,
You can configure your google Authorization Code from Settings > Configuration > General Settings by clicking on "Generate Google Authorization Code"
"""
}
