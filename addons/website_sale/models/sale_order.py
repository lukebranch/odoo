# -*- coding: utf-8 -*-
import random

from openerp import api, fields, models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    website_order_line = fields.One2many(
        'sale.order.line', 'order_id',
        string='Order Lines displayed on Website', readonly=True,
        help='Order Lines to be displayed on the website. They should not be used for computation purpose.',
    )
    cart_quantity = fields.Integer(compute='_compute_cart_info')
    payment_acquirer_id = fields.Many2one('payment.acquirer', 'Payment Acquirer', on_delete='set null', copy=False)
    payment_tx_id = fields.Many2one('payment.transaction', 'Transaction', on_delete='set null', copy=False)
    only_services = fields.Boolean(compute='_compute_cart_info')

    @api.depends('website_order_line')
    def _compute_cart_info(self):
        for order in self:
            order.cart_quantity = int(sum(order.mapped('website_order_line.product_uom_qty')))
            order.only_services = all(order.website_order_line.filtered(lambda l: (l.product_id and l.product_id.type == 'service')))

    def _get_errors(self):
        self.ensure_one()
        return []

    def _get_website_data(self):
        self.ensure_one()
        return {
            'partner': self.partner_id.id,
            'order': self
        }

    @api.multi
    def _cart_find_product_line(self, product_id=None, line_id=None, **kwargs):
        for so in self:
            domain = [('order_id', '=', so.id), ('product_id', '=', product_id)]
            if line_id:
                domain.append(('id', '=', line_id))
            return self.env['sale.order.line'].sudo().search(domain).ids

    @api.multi
    def _website_product_id_change(self, order_id, product_id, qty=0, line_id=None):
        self.ensure_one()
        so = self.env['sale.order'].browse(order_id)
        OrderLine = self.env['sale.order.line'].sudo()
        values = OrderLine.product_id_change(
            pricelist=so.pricelist_id.id,
            product=product_id,
            partner_id=so.partner_id.id,
            fiscal_position=so.fiscal_position.id,
            qty=qty,
        )['value']

        if line_id:
            line = OrderLine.browse(line_id)
            values['name'] = line.name
        else:
            product = self.env['product.product'].browse(product_id)
            values['name'] = product.display_name
            if product.description_sale:
                values['name'] += '\n'+product.description_sale

        values['product_id'] = product_id
        values['order_id'] = self.id
        if not values.get('tax_id'):
            values['tax_id'] = [(6, 0, values['tax_id'])]
        return values

    @api.multi
    def _cart_update(self, product_id=None, line_id=None, add_qty=0, set_qty=0, **kwargs):
        """ Add or set product quantity, add_qty can be negative """
        OrderLine = self.env['sale.order.line'].sudo()
        quantity = 0
        for so in self:
            if not line_id:
                lines = so._cart_find_product_line(product_id, line_id, kwargs=kwargs)
                if lines:
                    line_id = lines[0]
                else:
                    # Create line if no line with product_id can be located
                    values = so._website_product_id_change(so.id, product_id, qty=1)
                    line_id = OrderLine.create(values).id
                    if add_qty:
                        add_qty -= 1

            # compute new quantity
            line = OrderLine.browse(line_id)
            if set_qty:
                quantity = set_qty
            elif add_qty >= 0:
                quantity = line.product_uom_qty + add_qty
            # Remove zero of negative lines
            if quantity <= 0:
                line.unlink()
            else:
                # update line
                values = so._website_product_id_change(so.id, product_id, qty=quantity, line_id=line_id)
                values['product_uom_qty'] = quantity
                line.write(values)
        return {'line_id': line_id, 'quantity': quantity}

    def _cart_accessories(self):
        for order in self:
            s = (order.mapped('website_order_line.product_id.accessory_product_ids') - order.mapped('order_line.product_id')).ids
            product_ids = random.sample(s, min(len(s), 3))
            return self.env['product.product'].browse(product_ids)
