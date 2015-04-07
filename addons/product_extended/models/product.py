# -*- coding: utf-8 -*-

from openerp import api, models, fields


class ProductTemplate(models.Model):
    _inherit = 'product.template'


    @api.multi
    def compute_standard_price(self, recursive=False, real_time_accounting=False):
        MrpBom = self.env['mrp.bom']
        for product in self:
            pricedict = {}
            bom_id = MrpBom._bom_find(product_tmpl_id=product.id)
            if bom_id:
                bom = MrpBom.browse(bom_id)
                if recursive:
                    res = bom.bom_line_ids.mapped('product_id').compute_standard_price(recursive=recursive, real_time_accounting=real_time_accounting)
                price = product._compute_standard_price(bom, real_time_accounting=real_time_accounting)
                pricedict[product.id] = price
                if not self.env.context.get('no_update'):
                    if (product.valuation != "real_time" or not real_time_accounting):
                        product.write({'standard_price' : price})
                    else:
                        product.do_change_standard_price(price)
        return pricedict


    @api.multi
    def _compute_standard_price(self, bom, real_time_accounting=False):
        price = 0
        ProductUom = self.env['product.uom']
        for sbom in bom.bom_line_ids:
            my_qty = sbom.product_qty
            if not sbom.attribute_value_ids:
                # No attribute_value_ids means the bom line is not variant specific
                price += ProductUom._compute_price(sbom.product_id.uom_id.id, sbom.product_id.standard_price, sbom.product_uom.id) * my_qty

        if bom.routing_id:
            for wline in bom.routing_id.workcenter_lines:
                wc = wline.workcenter_id
                cycle = wline.cycle_nbr
                hour = (wc.time_start + wc.time_stop + cycle * wc.time_cycle) *  (wc.time_efficiency or 1.0)
                price += wc.costs_cycle * cycle + wc.costs_hour * hour
                price = ProductUom._compute_price(bom.product_uom.id, price, bom.product_id.uom_id.id)
        
        #Convert on product UoM quantities
        if price > 0:
            price = ProductUom._compute_price(bom.product_uom.id, price / bom.product_qty, bom.product_id.uom_id.id)

        return price

class ProductProduct(models.Model):

    _inherit = 'product.product'

    @api.multi
    def compute_standard_price(self, recursive=False, real_time_accounting=False):
        MrpBom = self.env['mrp.bom']
        for product in self:
            bom_id = MrpBom._bom_find(product_id=product.id)
            if bom_id:
                bom = MrpBom.browse(bom_id)
                if recursive:
                    res = bom.bom_line_ids.mapped('product_id').compute_standard_price(recursive=recursive, real_time_accounting=real_time_accounting)
                price = product._compute_standard_price(bom, real_time_accounting=real_time_accounting)

                if not self.env.context.get('no_update'):
                    if (product.valuation != "real_time" or not real_time_accounting):
                        product.write({'standard_price' : price})
                    else:
                        product.do_change_standard_price(price)
        return True


    @api.multi
    def _compute_standard_price(self, bom, real_time_accounting=False):
        price = 0
        ProductUom = self.env['product.uom']
        for sbom in bom.bom_line_ids:
            my_qty = sbom.product_qty
            if not sbom.attribute_value_ids:
                # No attribute_value_ids means the bom line is not variant specific
                price += ProductUom._compute_price(sbom.product_id.uom_id.id, sbom.product_id.standard_price, sbom.product_uom.id) * my_qty

        if bom.routing_id:
            for wline in bom.routing_id.workcenter_lines:
                wc = wline.workcenter_id
                cycle = wline.cycle_nbr
                hour = (wc.time_start + wc.time_stop + cycle * wc.time_cycle) *  (wc.time_efficiency or 1.0)
                price += wc.costs_cycle * cycle + wc.costs_hour * hour
                price = ProductUom._compute_price(bom.product_uom.id, price, bom.product_id.uom_id.id)

        #Convert on product UoM quantities
        if price > 0:
            price = ProductUom._compute_price(bom.product_uom.id, price / bom.product_qty, bom.product_id.uom_id.id)

        return price
