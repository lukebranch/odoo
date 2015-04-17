# -*- coding: utf-8 -*-

{
    'name': 'Drop Shipping',
    'version': '1.0',
    'category': 'Warehouse Management',
    'summary': 'Drop Shipping',
    'description': """
Manage drop shipping orders
===========================

This module adds a pre-configured Drop Shipping picking type
as well as a procurement route that allow configuring Drop
Shipping products and orders.

When drop shipping is used the goods are directly transferred
from suppliers to customers (direct delivery) without
going through the retailer's warehouse. In this case no
internal transfer document is needed.

""",
    'author': 'Odoo S.A.',
    'website': 'https://www.odoo.com/page/warehouse',
    'depends': ['purchase', 'sale_stock'],
    'data': ['views/stock_dropshipping.xml'],
    'installable': True,
}
