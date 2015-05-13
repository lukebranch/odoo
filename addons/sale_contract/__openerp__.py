{
    'name': 'Extra Contracts Management',
    'version': '1.0',
    'category': 'Sales Management',
    'description': """
Odoo Extra Menu taking all modifs made to account_analytic_analysis for contract management""",
    'author': 'Odoo S.A.',
    'website': 'https://www.odoo.com/',
    'depends': ['account_analytic_analysis', 'hr_timesheet_invoice'],
    'data': [
        'report/sale_contract_report_view.xml',
        'security/sale_contract_security.xml',
        'security/ir.model.access.csv',
        'data/sale_contract_data.xml',
        'views/analytic_view.xml',
        'views/sale_contract_view.xml',
        'views/hr_timesheet_invoice_view.xml',
        'views/product_template_view.xml'
    ],
    'installable': True,
    'auto_install': False,
}