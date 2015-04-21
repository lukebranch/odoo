# -*- coding: utf-8 -*-

{
    'name': 'Warehouse Management: Waves',
    'version': '1.0',
    'category': 'Stock Management',
    'description': """
This module adds the picking wave option in warehouse management.
=================================================================
    """,
    'author': 'Odoo S.A.',
    'website': 'https://www.odoo.com/page/warehouse',
    'depends': ['stock'],
    'data': ['security/ir.model.access.csv',
            'views/stock_picking_wave_view.xml',
            'views/stock_picking_wave_data.xml',
            'views/stock_picking_wave_sequence.xml',
            'wizard/picking_to_wave_view.xml',
            'views/stock_picking_wave_demo.xml',
             ],
    'installable': True,
}
