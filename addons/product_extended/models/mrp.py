# -*- coding: utf-8 -*-

from openerp import api, models, fields

class ProductBom(models.Model):
    _inherit = 'mrp.bom'
            
    standard_price = fields.Float(related='product_tmpl_id.standard_price', string="Standard Price")

