# -*- coding: utf-8 -*-

{
    'name': 'Account Contract Dashboard',
    'version': '1.0',
    'depends': ['account_analytic_analysis', 'account_asset', 'website'],
    'author': 'Odoo S.A.',
    'description': """
Accounting Contract Dashboard
========================
It adds dashboards to :
1) Analyse the recurrent revenue and other metrics for contracts
2) Analyse the contracts modifications by salesman and calculate their value.
    """,
    'website': 'https://www.odoo.com/page/accounting',
    'category': 'Accounting & Finance',
    'data': [
        'views/account_contract_dashboard_report_view.xml',
        'templates/dashboard.xml',
        'templates/assets.xml',
    ],
    'qweb': ['static/src/xml/*.xml'],
    'installable': True,
    'application': False,
}
