# -*- coding: utf-8 -*-

{
    'name': 'WMS Landed Costs',
    'version': '1.1',
    'author': 'Odoo S.A.',
    'summary': 'Landed Costs',
    'description': """
Landed Costs Management
=======================
This module allows you to easily add extra costs on pickings and decide the split of these costs among their stock moves in order to take them into account in your stock valuation.
    """,
    'website': 'https://www.odoo.com/page/warehouse',
    'depends': ['stock_account'],
    'category': 'Warehouse Management',
    'sequence': 16,
    'demo': [
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/stock_landed_costs_sequence.xml',
        'views/product_view.xml',
        'views/stock_landed_costs_view.xml',
        'views/stock_landed_costs_data.xml',
    ],
    'installable': True,
}
