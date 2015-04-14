# -*- coding: utf-8 -*-
{
    'name': 'Website Sale Digital - Sell digital products',
    'version': '1.0',
    'description': """
Sell digital product using attachments to virtual products
""",
    'author': 'Odoo S.A.',
    'depends': [
        'document',
        'website_sale',
    ],
    'installable': True,
    'data': [
        'views/templates.xml',
        'views/product_template_view.xml',
    ],
    'demo': [
        'data/product_template_demo.xml',
        'data/ir_attachment_demo.xml'
    ],
}
