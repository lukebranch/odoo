# -*- encoding: utf-8 -*-
from openerp import models, fields, api
from openerp.addons.sale.res_config import sale_configuration

class website_sale_configuration(models.TransientModel):
    _inherit = 'sale.config.settings'

    module_website_sale_digital = fields.Boolean('Sell digital products', 
        help="Allow you to set mark a product as a digital product, allowing customers that have purchased the product to download its attachments. This installs the module website_sale_digital.")


class website_config(models.TransientModel):
    _inherit = 'website.config.settings'

    products_per_page = fields.Integer('Products per page in the Shop Frontend', help="Number of products per page")
    products_per_row = fields.Integer('Products per row in the Shop Frontend', help="Number of lines per row")

    @api.multi
    def set_website(self):
        self.ensure_one()
        self.website_id.products_per_row = self.products_per_row
        self.website_id.products_per_page = self.products_per_page