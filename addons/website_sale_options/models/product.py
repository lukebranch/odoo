# -*- coding: utf-8 -*-
from openerp import models, fields


class ProductTemplate(models.Model):
    _inherit = "product.template"

    optional_product_ids = fields.Many2many('product.template', 'product_optional_rel', 'src_id', 'dest_id', string='Optional Products', help="Products to propose when add to cart.")
