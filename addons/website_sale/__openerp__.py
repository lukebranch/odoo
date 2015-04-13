# -*- coding: utf-8 -*-
{
    'name': 'eCommerce',
    'category': 'Website',
    'summary': 'Sell Your Products Online',
    'website': 'https://www.odoo.com/page/e-commerce',
    'version': '1.0',
    'description': """
Odoo E-Commerce
==================

        """,
    'author': 'Odoo SA',
    'depends': ['website', 'sale', 'payment'],
    'data': [
        'data/crm_team_data.xml',
        'data/ir_actions_data.xml',
        'data/product_style_data.xml',
        'data/website_menu_data.xml',
        'views/product_views.xml',
        'views/templates.xml',
        'views/payment_transaction.xml',
        'views/sale_order.xml',
        'views/snippets.xml',
        'views/report_shop_saleorder.xml',
        'views/sale_config_settings_view.xml',
        'security/ir.model.access.csv',
        'security/ir_rule_security.xml',
        'security/res_groups_security.xml',
    ],
    'demo': [
        'data/product_demo.xml',
        'data/crm_team_demo.xml',
    ],
    'qweb': ['static/src/xml/*.xml'],
    'installable': True,
    'application': True,
}
