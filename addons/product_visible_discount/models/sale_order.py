# -*- coding: utf-8 -*-

from openerp import api, fields, models


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    @api.multi
    def product_id_change(self, pricelist, product, qty=0,
            uom=False, qty_uos=0, uos=False, name='', partner_id=False,
            lang=False, update_tax=True, date_order=False, packaging=False,
            fiscal_position=False, flag=False):

        def get_real_price(res_dict, product_id, qty, uom, pricelist):
            """Retrieve the price before applying the pricelist"""

            field_name = 'list_price'
            rule_id = res_dict.get(pricelist) and res_dict[pricelist][1] or False
            if rule_id:
                item_base = PriceItem.browse(rule_id).base
                if item_base > 0:
                    field_name = PriceType.browse(item_base).field

            factor = 1.0
            if uom and uom != product.uom_id.id:
                # the unit price is in a different uom
                factor = self.env['product.uom']._compute_qty(uom, 1.0, product.uom_id.id)
            return getattr(product, field_name) * factor

        PriceItem = self.env['product.pricelist.item']
        PriceType = self.env['product.price.type']
        Product = self.env['product.product']
        res = super(SaleOrderLine, self).product_id_change(pricelist, product, qty,
            uom, qty_uos, uos, name, partner_id,
            lang, update_tax, date_order, packaging=packaging, fiscal_position=fiscal_position, flag=flag)

        price_unit = res['value'].get('price_unit', False)
        if not (price_unit and product and pricelist and self.env['res.users'].has_group('sale.group_discount_per_so_line')):
            return res
        Currency = self.env['res.currency']
        uom = res['value'].get('product_uom', uom)
        product = Product.browse(product)
        product_price = self.env['product.pricelist'].browse(pricelist)
        list_price = product_price.price_rule_get(
                product.id, qty or 1.0, partner_id)

        new_list_price = get_real_price(list_price, product.id, qty, uom, pricelist)
        if product_price.visible_discount and list_price[pricelist][0] != 0 and new_list_price != 0:
            if product.company_id and product_price.currency_id.id != product.company_id.currency_id.id:
                # new_list_price is in company's currency while price in pricelist currency
                new_list_price = Currency.compute(
                    product.company_id.currency_id.id, product_price.currency_id.id,
                    new_list_price)
            discount = (new_list_price - price_unit) / new_list_price * 100
            if discount > 0:
                price_unit = new_list_price
                discount = discount
        if discount:
            res['value']['price_unit'] = price_unit
            res['value']['discount'] = discount
        return res
