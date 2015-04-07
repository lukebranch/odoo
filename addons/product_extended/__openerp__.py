# -*- coding: utf-8 -*-

{
    "name" : "Product extension to track sales and purchases",
    "version" : "1.0",
    "author" : "Odoo S.A.",
    'website': 'https://www.odoo.com',
    "depends" : ["product", "purchase", "sale", "mrp", "stock_account"],
    "category" : "Generic Modules/Inventory Control",
    "description": """
Product extension. This module adds:
  * Computes standard price from the BoM of the product with a button on the product variant based
    on the materials in the BoM and the work centers.  It can create the necessary accounting entries when necessary.
""",
    "init_xml" : [],
    "demo_xml" : [],
    "data" : [
        'wizard/wizard_price_views.xml',
        'views/product_views.xml',
        'views/mrp_views.xml',
        'security/ir.model.access.csv'
    ],
    "active": False,
    "installable": True
}
