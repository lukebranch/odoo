# -*- encoding: utf-8 -*-

{
    'name': 'Account Contract Dashboard',
    'version': '1.0',
    'depends': ['account_analytic_analysis', 'account_asset'],
    'author': 'Odoo S.A.',
    'description': """
    Account Contract Dashboard
    """,
    'website': 'https://www.odoo.com/page/accounting',
    'category': 'Accounting & Finance',
    'demo': [],
    'data': [
        # 'security/account_contract_dashboard.xml',
        # 'security/ir.model.access.csv',
        'report/account_contract_dashboard_report_view.xml',
    ],
    # 'qweb': [
    #     "static/src/xml/account_asset_template.xml",
    # ],
    'installable': True,
    'application': False,
}
