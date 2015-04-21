# -*- coding: utf-8 -*-

from openerp import fields, models

SPLIT_METHOD = [
    ('equal', 'Equal'),
    ('by_quantity', 'By Quantity'),
    ('by_current_cost_price', 'By Current Cost Price'),
    ('by_weight', 'By Weight'),
    ('by_volume', 'By Volume'),
]

class ProductTemplate(models.Model):
    _inherit = "product.template"

    landed_cost_ok = fields.Boolean('Can constitute a landed cost', default=False)
    split_method = fields.Selection(SPLIT_METHOD, default='equal')
