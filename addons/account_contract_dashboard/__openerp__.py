# -*- coding: utf-8 -*-

{
    'name': 'Account Contract Dashboard',
    'version': '1.0',
    'depends': ['account_analytic_analysis', 'account_asset', 'website'],
    'author': 'Odoo S.A.',
    'description': """
    Account Contract Dashboard
    """,
    'website': 'https://www.odoo.com/page/accounting',
    'category': 'Accounting & Finance',
    'data': [
        'report/account_contract_dashboard_report_view.xml',
        'templates/dashboard.xml',
        'templates/assets.xml',
        'templates/home.xml',
    ],
    'qweb': ['static/src/xml/*.xml'],
    'installable': True,
    'application': False,
}
