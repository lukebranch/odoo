# -*- coding: utf-8 -*-
from dateutil.relativedelta import relativedelta
from datetime import datetime
from openerp.exceptions import UserError

import hashlib
import math
import random


from openerp import models, fields, api, _
from openerp.exceptions import MissingError


class SaleApplicability(models.Model):
    _name = 'sale.applicability'
    _description = "Sales Coupon Applicability"

    partner_id = fields.Many2one('res.partner', string="Limit to a single customer", help="Coupon program will work only for the perticular selected customer")
    date_from = fields.Date("Date From", help="Date on which coupon will get activated", default=fields.date.today())
    date_to = fields.Date("Date To", help="Date after which coupon will get deactivated", default=fields.date.today() + relativedelta(days=1))
    validity_type = fields.Selection(
        [('day', 'Day(s)'),
         ('week', 'Week(s)'),
         ('month', 'Month(s)'),
         ('year', 'Year(s)'),
         ], string='Validity Type', required=True, default='day',
        help="Validity Type can be based on either day, month, week or year.")
    validity_duration = fields.Integer("Validity Duration", default=1, help="Validity duration can be set according to validity type")
    expiration_use = fields.Integer("Expiration use", default=1, help="Number of Times coupon can be Used")
    purchase_type = fields.Selection([('product', 'Product'), ('category', 'Category'),
                                      ('amount', 'Amount')], string="Type", required=True, default="product")
    product_id = fields.Many2one('product.product', string="Product")
    product_category_id = fields.Many2one('product.category', string="Product Categoy")
    product_quantity = fields.Integer("Quantity", default=1)
    product_uom_id = fields.Many2one('product.uom', string="UoM", readonly=True)
    # product_uom_id = fields.Char('Product UoM', readonly=True)
    minimum_amount = fields.Float(string="Amount", help="Alteast amount, for that customer have to purchase to get the reward")
    applicability_tax = fields.Selection([('tax_included', 'Tax included'), ('tax_excluded', 'Tax excluded')], default="tax_excluded")
    company_id = fields.Many2one('res.company', string="Company", default=lambda self: self.env.user.company_id)
    currency_id = fields.Many2one("res.currency", readonly=True, default=lambda self: self.env.user.company_id.currency_id.id)

    def get_uom_of_reward_on_specific_product(self):
        self.reward_discount_on_product_uom_id = self.reward_discount_on_product_id.product_tmpl_id.uom_id

    def get_expiration_date(self, start_date):
        if self.validity_type == 'day':
            return start_date + relativedelta(days=(self.validity_duration))
        if self.validity_type == 'month':
            return start_date + relativedelta(months=self.validity_duration)
        if self.validity_type == 'week':
            return start_date + relativedelta(days=(self.validity_duration * 7))
        if self.validity_type == 'year':
            return start_date + relativedelta(months=(self.validity_duration * 12))


class SaleReward(models.Model):
    _name = 'sale.reward'
    _description = "Sales Coupon Rewards"

    reward_type = fields.Selection([('product', 'Product'),
                                    ('discount', 'Discount'),
                                    ('coupon', 'Coupon')], string="Free gift", help="Type of reward to give to customer", default="product", required=True)
    reward_shipping_free = fields.Selection([('yes', 'Yes'), ('no', 'No')], string="Free Shipping", default="no", help="Shipment of the order is free or not")
    reward_product_product_id = fields.Many2one('product.product', string="Product")
    reward_quantity = fields.Integer(string="Quantity", default=1)
    reward_product_uom_id = fields.Many2one('product.uom', string="UoM", readonly=True)
    reward_gift_coupon_id = fields.Many2one('sale.couponprogram', string="Coupon program")
    reward_discount_type = fields.Selection([('no', 'No'), ('percentage', 'Percentage'),
                                             ('amount', 'Amount')], string="Apply a discount", default="no")
    reward_discount_percentage = fields.Float("Discount", help='The discount in percentage')
    reward_discount_amount = fields.Float("Discount", help='The discount in fixed amount')
    reward_discount_on = fields.Selection([('cart', 'On cart'), ('cheapest_product', 'On cheapest product'),
                                           ('specific_product', 'On specific product')], string="Discount On", default="cart")
    reward_discount_on_product_id = fields.Many2one('product.product', string="Product")
    reward_discount_on_product_uom_id = fields.Many2one('product.uom', string="UoM", readonly=True)
    reward_tax = fields.Selection([('tax_included', 'Tax included'),
                                   ('tax_excluded', 'Tax excluded')], string="Tax", default="tax_excluded")
    reward_partial_use = fields.Selection([('yes', 'Yes'), ('no', 'No')], default="no", string="Partial use", help="The reward can be used partially or not")
    reward_currency_id = fields.Many2one("res.currency", readonly=True, default=lambda self: self.env.user.company_id.currency_id)


class SaleCoupon(models.Model):
    _name = 'sale.coupon'
    _description = "Sales Coupon"

    program_id = fields.Many2one('sale.couponprogram', string="Program")
    coupon_code = fields.Char(string="Coupon Code",
                              default=lambda self: 'SC' + (hashlib.sha1(str(random.getrandbits(256)).encode('utf-8')).hexdigest()[:7]).upper(),
                              required=True, readonly=True, help="Coupon Code")
    nbr_used = fields.Integer(string="Total used")
    nbr_uses = fields.Integer(string="Number of times coupon can be use")
    order_line_id = fields.One2many('sale.order.line', 'coupon_id', string="Sale order line")
    state = fields.Selection([
                             ('new', 'New'),
                             ('used', 'Used'),
                             ('expired', 'Expired')],
                             'Status', required=True, copy=False, track_visibility='onchange',
                             default='new')
    ean13 = fields.Char(string="Bar Code")
    origin = fields.Char(string="Origin", help="Coupon is originated from")
    origin_order_id = fields.Many2one('sale.order', string='Order Reference', readonly=True, help="The Sales order id from which coupon is generated")
    reward_name = fields.Char(string="Reward", help="Reward on coupon")


class SaleCouponProgram(models.Model):
    _name = 'sale.couponprogram'
    _description = "Sales Coupon Program"
    _inherits = {'sale.applicability': 'applicability_id', 'sale.reward': 'reward_id'}
    name = fields.Char(help="Program name", required=True)
    # program_code = fields.Char(string='Coupon Code',
    #                            default=lambda self: 'SC' +
    #                                                 (hashlib.sha1(
    #                                                  str(random.getrandbits(256)).encode('utf-8')).hexdigest()[:7]).upper(),
    #                            required=True,, help="Coupon Code", store=True)
    program_code = fields.Char(string="Program Code")
    program_type = fields.Selection([('apply_immediately', 'Apply Immediately'), ('public_unique_code',
                                     'Public Unique Code'), ('generated_coupon', 'Generated Coupon')],
                                    string="Program Type", help="The type of the coupon program", required=True, default="apply_immediately")
    active = fields.Boolean(string="Active", default=True, help="Coupon program is active or inactive")
    program_sequence = fields.Integer(string="Sequence", help="According to sequence, one rule is selected from multiple defined rules to apply")
    coupon_ids = fields.One2many('sale.coupon', 'program_id', string="Coupon Id")
    applicability_id = fields.Many2one('sale.applicability', string="Applicability Id", ondelete='cascade', required=True)
    reward_id = fields.Many2one('sale.reward', string="Reward", ondelete='cascade', required=True)
    count_sale_order = fields.Integer(compute='_compute_so_count', default=0)
    count_coupons = fields.Integer(compute='_compute_coupon_count', default=0)
    state = fields.Selection([('draft', 'Draft'), ('opened', 'Opened'), ('closed', 'Closed')], help="Shows the program states", default="draft")

    _sql_constraints = [
        ('unique_program_code', 'unique(program_code)', 'The program code must be unique!'),
    ]

    @api.multi
    def open_generate_coupon_wizard(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Number of coupons',
            'res_model': 'sale.manual.coupon',
            'view_mode': 'form',
            'views': [(False, 'form')],
            'target': 'new',
        }

    @api.one
    def action_opened(self):
        self.state = 'opened'

    @api.one
    def action_closed(self):
        for coupon in self.env['sale.coupon'].search([('program_id', '=', self.id)]):
            coupon.state = 'expired'
        self.state = 'closed'

    @api.one
    def action_draft(self):
        self.state = 'opened'

    def _compute_so_count(self):
        count = 0
        sales_order_line = self.env['sale.order.line'].search([('coupon_program_id', '=', self.id)])
        if sales_order_line:
            for order in sales_order_line:
                count += 1
        self.count_sale_order = count

    def _compute_coupon_count(self):
        count = 0
        coupons = self.env['sale.coupon'].search([('program_id', '=', self.id)])
        if coupons:
            for coupon in coupons:
                count += 1
        self.count_coupons = count

    @api.onchange('product_id')
    def get_uom_of_applicable_product(self):
        self.product_uom_id = self.product_id.product_tmpl_id.uom_id

    @api.onchange('reward_product_product_id')
    def get_uom_of_reward_product(self):
        self.reward_product_uom_id = self.reward_product_product_id.product_tmpl_id.uom_id

    @api.onchange('reward_discount_on_product_id')
    def get_uom_of_reward_on_specific_product(self):
        self.reward_discount_on_product_uom_id = self.reward_discount_on_product_id.product_tmpl_id.uom_id

    def check_is_program_expired(self, coupon_code):
        if self.program_type == 'generated_coupon' or self.program_type == 'apply_immediately':
            if fields.date.today() > self.applicability_id.get_expiration_date(datetime.strptime(self.create_date, "%Y-%m-%d %H:%M:%S").date()):
                return True
            else:
                coupon_obj = self.env['sale.coupon'].search([('coupon_code', '=', coupon_code)])
                if coupon_obj:
                    coupon_obj.state = 'expired'
                return False
        if self.program_type == 'public_unique_code':
            if fields.date.today() > datetime.strptime(self.date_to, "%Y-%m-%d").date():
                return True
            else:
                coupon_obj = self.env['sale.coupon'].search([('coupon_code', '=', coupon_code)])
                if coupon_obj:
                    coupon_obj.state = 'expired'
                return False

    def check_is_program_closed(self):
        if self.state == 'closed':
            return True

    @api.multi
    def action_view_order(self, context=None):
        res = self.env['ir.actions.act_window'].for_xml_id('website_sale_coupon', 'action_order_line_product_tree', context=context)
        res['domain'] = [('coupon_program_id', '=', self.id)]
        return res

    @api.multi
    def action_view_coupons(self, context=None):
        res = self.env['ir.actions.act_window'].for_xml_id('website_sale_coupon', 'action_coupon_tree', context=context)
        res['domain'] = [('program_id', '=', self.id)]
        return res


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    coupon_id = fields.Char(string="Coupon")
    coupon_program_id = fields.Many2one('sale.couponprogram', string="Coupon program")
    generated_from_line_id = fields.Many2one('sale.order.line')

    @api.multi
    def unlink(self):
        res = True
        try:
            for line in self:
                if line.coupon_id:
                    coupon_obj = self.env['sale.coupon'].search([('coupon_code', '=', line.coupon_id)])
                    if coupon_obj:
                        coupon_obj.state = 'new'
                        coupon_obj.reward_name = ""
                        if coupon_obj.nbr_used > 1:
                            coupon_obj.nbr_used -= 1
                        else:
                            coupon_obj.nbr_used = 0
            reward_lines = self.order_id.order_line.filtered(lambda x: x.generated_from_line_id.id in self.ids)
            for line_obj in self:
                line = self.order_id.order_line.filtered(lambda x: x.generated_from_line_id.id is False and (x.coupon_program_id.reward_product_product_id == line_obj.product_id or x.coupon_program_id.reward_discount_on_product_id == line_obj.product_id))
                if line:
                    reward_lines += line
            if reward_lines:
                reward_lines.unlink()
            res = super(SaleOrderLine, self).unlink()
        except MissingError:
            pass
        return res

    @api.multi
    def apply_immediately_reward(self):
        programs = self._search_reward_programs([('program_type', '=', 'apply_immediately'), ('state', '=', 'opened')])
        if programs:
            self.process_rewards(programs, False)
        return programs

    def _search_reward_programs(self, domain=[]):
        return self.env['sale.couponprogram'].search(domain + [
            '&', ('product_quantity', '<=', self.product_uom_qty),
            '|',
            '&', ('purchase_type', '=', 'product'), ('product_id', '=', self.product_id.id),
            '&', ('purchase_type', '=', 'category'), ('product_category_id', '=', self.product_id.categ_id.id),
            '|', ('partner_id', '=', None), ('partner_id', '=', self.order_id.partner_id.id)])
  # return self.env['sale.couponprogram'].search(domain + [
  #           '&', ('product_quantity', '<=', self.product_uom_qty),
  #           '|',
  #           '&', ('purchase_type', '=', 'product'), ('product_id', '=', self.product_id.id),
  #           '&', ('purchase_type', '=', 'category'), ('product_category_id', '=', self.product_id.categ_id.id)])

    @api.multi
    def process_rewards(self, programs, coupon_code):
        for program in programs:
            getattr(self, '_process_reward_' + program.reward_type)(program, coupon_code)

    def _create_discount_reward(self, program, qty, discount_amount, coupon_code):
        reward_product_id = self.env.ref('website_sale_coupon.product_product_reward').id
        reward_lines = self.order_id.order_line.filtered(lambda x: x.generated_from_line_id == self and x.product_id.id == reward_product_id and x.coupon_program_id == program)
        if discount_amount <= 0 and reward_lines:
            reward_lines.unlink()
        elif discount_amount > 0 and reward_lines:
            for reward_line in reward_lines:
                reward_line.with_context(noreward=True).write({'price_unit': -discount_amount, 'product_uom_qty': qty})
        if discount_amount > 0 and not reward_lines:
            if program.purchase_type == 'product':
                desc = _("Reward on ") + program.product_id.name
            if program.purchase_type == 'category':
                desc = _("Reward on category of ") + self.product_id.name
            if coupon_code:
                desc = desc + " using code " + coupon_code
            vals = {
                'product_id': reward_product_id,
                'name': desc,
                'product_uom_qty': qty,
                'price_unit': -discount_amount,
                'order_id': self.order_id.id,
                'coupon_program_id': program.id,
                'generated_from_line_id': self.id,
                'coupon_id': coupon_code
            }
            self.with_context(noreward=True).create(vals)
            if coupon_code:
                coupon_obj = self.env['sale.coupon'].search([('coupon_code', '=', coupon_code)])
                if coupon_obj:
                    coupon_obj.state = 'used'
                    #coupon_obj.order_line_id = self.id
                    coupon_obj.nbr_used = coupon_obj.nbr_used + 1
                    coupon_obj.reward_name = desc

    def _process_reward_product(self, program, coupon_code):
        product_lines = self.order_id.order_line.filtered(lambda x: x.product_id == program.reward_product_product_id)
        vals = self.product_id_change(self.order_id.pricelist_id.id, program.reward_product_product_id.id, program.reward_quantity,
                                      uom=program.reward_product_uom_id.id)['value']
        if product_lines:
            line = product_lines[0]
        if program.reward_product_product_id == program.product_id:
            to_reward_qty = math.floor(self.product_uom_qty / (program.product_quantity + program.reward_quantity))
            if not (to_reward_qty) and (line.product_uom_qty == program.product_quantity):
                product_qty = line.product_uom_qty + program.reward_quantity
                line.with_context(nocoupon=True).write({'product_uom_qty': product_qty})
                to_reward_qty = 1
        else:
            to_reward_qty = math.floor(self.product_uom_qty / program.product_quantity * program.reward_quantity)
        if not to_reward_qty:
            vals['price_unit'] = 0
        if not product_lines:
            vals['product_id'] = program.reward_product_product_id.id
            vals['product_uom_qty'] = to_reward_qty
            vals['order_id'] = self.order_id.id
            vals['coupon_id'] = coupon_code
            line = self.with_context(noreward=True).create(vals)
        else:
            if program.reward_product_product_id.id == line.product_id.id and \
               program.reward_product_product_id != program.product_id and line.product_uom_qty <= to_reward_qty:
                    line.with_context(noreward=True).write({'product_uom_qty': to_reward_qty})
        self._create_discount_reward(program, to_reward_qty, vals['price_unit'], coupon_code)

    def _process_reward_discount(self, program, coupon_code):
        discount_amount = 0
        if program.reward_discount_type == 'amount':
            discount_amount = program.reward_discount_amount
        elif program.reward_discount_type == 'percentage':
            if program.reward_discount_on == 'cart':
                discount_amount = self.order_id.amount_total * (program.reward_discount_percentage / 100)
            elif program.reward_discount_on == 'cheapest_product':
                    unit_prices = [x.price_unit for x in self.order_id.order_line if x.coupon_program_id.id is False]
                    discount_amount = (min(unit_prices) * (program.reward_discount_percentage) / 100)
            elif program.reward_discount_on == 'specific_product':
                #reward_qty = self.product_uom_qty / (program.product_quantity * program.reward_quantity)
                discount_amount = sum([x.price_unit * (program.reward_discount_percentage / 100) for x in self.order_id.order_line if x.product_id == program.reward_discount_on_product_id])
        self._create_discount_reward(program, 1, discount_amount, coupon_code)


class SaleOrder(models.Model):
    _inherit = "sale.order"

    coupon_program_id = fields.Many2one('sale.couponprogram', string="Coupon program")

    @api.model
    def create(self, vals):
        res = super(SaleOrder, self).create(vals)
        res._merge_duplicate_product_line()
        if vals.get('order_line'):
            res.apply_immediately_reward()
        return res

    @api.multi
    def write(self, vals):
        if not self.is_reward_line_updated(vals):
            res = super(SaleOrder, self).write(vals)
            self._merge_duplicate_product_line()
            print "<<<<<<<<<<>>>>>>>> ttl amt", self.amount_total
            if vals.get('order_line'):
                self.apply_immediately_reward()
            return res
        return True

    @api.multi
    def _cart_update(self, product_id=None, line_id=None, add_qty=0, set_qty=0, **kwargs):
        res = super(SaleOrder, self)._cart_update(product_id, line_id, add_qty, set_qty)
        self.apply_immediately_reward()
        return res

    @api.multi
    def _merge_duplicate_product_line(self):
        product_line = []
        line_to_remove = []
        for line in self.order_line:
            if line.product_id.id != self.env.ref('website_sale_coupon.product_product_reward').id:
                product_line = self.order_line.filtered(lambda x: x.product_id == line.product_id and x.id != line.id)
                for p_line in product_line:
                    if p_line and (line not in line_to_remove):
                        line.with_context(nocoupon=True).write({'product_uom_qty': line.product_uom_qty + p_line.product_uom_qty})
                        line_to_remove += p_line
        if line_to_remove:
            for line in line_to_remove:
                line.unlink()

    def is_reward_line_updated(self, vals):
        if vals.get('order_line'):
            for order_line in vals.get('order_line'):
                if order_line[2] is not False and self.order_line.browse(order_line[1]).product_id == self.env.ref('website_sale_coupon.product_product_reward'):
                    #vals['order_line'][0][2] = False
                    return True

    def _search_reward_programs(self, domain=[]):
        program = self.env['sale.couponprogram'].search(domain + [
            '&', ('purchase_type', '=', 'amount'), '|',
            '&', ('reward_tax', '=', 'tax_excluded'), ('minimum_amount', '<=', self.amount_total),
            '&', ('reward_tax', '=', 'tax_included'), ('minimum_amount', '<=', self.amount_untaxed)], limit=1)
        if not program:
            reward_line = self.order_line.filtered(lambda x: x.generated_from_line_id.id is False and x.product_id == self.env.ref('website_sale_coupon.product_product_reward'))
            if reward_line:
                domain += [('reward_discount_on', '!=', 'cheapest_product'), ('reward_discount_on', '!=', 'specific_product'), ('reward_type', '=', 'discount')]
                program = self.env['sale.couponprogram'].search(domain + [
                    '&', ('purchase_type', '=', 'amount'), '|',
                    '&', ('reward_tax', '=', 'tax_excluded'), ('minimum_amount', '<=', self.amount_total - reward_line.price_unit),
                    '&', ('reward_tax', '=', 'tax_included'), ('minimum_amount', '<=', self.amount_untaxed - reward_line.price_unit)], limit=1)
        if program and program.partner_id.id is True:
            if self.partner_id == program.partner_id:
                return program
        if program and program.partner_id.id is False:
            return program
        else:
            return False

    def _check_current_reward_applicability(self, domain=[]):
        remove_reward_lines = []
        for order in self.filtered(lambda x: x.order_line is not False):
            reward_line = order.order_line.filtered(lambda x: x.coupon_program_id.purchase_type == 'amount' and x.coupon_program_id.program_type == domain[0][2])
            if reward_line:
                program = reward_line.coupon_program_id
                #check for customer
                if program.partner_id.id:
                    if program.partner_id != self.partner_id:
                        remove_reward_lines += reward_line
                if program.reward_discount_on == 'cart' and \
                   program.reward_discount_type == 'percentage' and \
                   program.reward_type == 'discount':
                    print "JJJJJdsfvergJJJJJJ", self.amount_total, program.minimum_amount
                    if program.applicability_tax == 'tax_excluded'and \
                       order.amount_total + ((-1) * reward_line.price_unit) < program.minimum_amount:
                            remove_reward_lines += reward_line
                    if program.applicability_tax == 'tax_included' and \
                       order.amount_untaxed + ((-1) * reward_line.price_unit) < program.minimum_amount:
                            remove_reward_lines += reward_line
                else:
                    #check for total amt
                    print "JJJJJJJJJJJ", self.amount_total, program.minimum_amount
                    if self.amount_total < program.minimum_amount:
                        remove_reward_lines += reward_line
            for order_line in [x for x in order.order_line if not (x.coupon_program_id or x.generated_from_line_id)]:
                programs = order_line._search_reward_programs(domain)
                if programs:
                    if programs.reward_type == 'product' or (programs.reward_type == 'discount' and programs.reward_discount_on == 'specific_product'):
                        product_line = self.order_line.filtered(lambda x: x.product_id == programs.reward_product_product_id or x.product_id == programs.reward_discount_on_product_id)
                        if not product_line:
                            reward_line = self.order_line.filtered(lambda x: x.coupon_program_id == programs and x.generated_from_line_id == order_line)
                            remove_reward_lines += reward_line
                if not programs:
                    remove_reward_lines += self.order_line.filtered(lambda x: x.generated_from_line_id == order_line and x.coupon_program_id.id is not False and x.coupon_program_id.program_type == domain[0][2])
        for remove_line in remove_reward_lines:
            remove_line.with_context(nocoupon=True).unlink()

    def _check_for_free_shipping(self, coupon_code):
        free_shipping_product_line = self.order_line.filtered(lambda x: x.product_id.is_delivery_chargeble is True)
        if not free_shipping_product_line:
            return True
        product_line = free_shipping_product_line[0]
        delivery_charge_line = self.order_line.filtered(lambda x: x.product_id == self.env.ref('delivery.product_product_delivery'))
        if not delivery_charge_line:
            reward_line = self.order_line.filtered(lambda x: x.product_id == self.env.ref('website_sale_coupon.product_product_reward') and
                                                   x.generated_from_line_id.product_id == self.env.ref('website_sale_coupon.product_product_reward'))
            if reward_line:
                reward_line.unlink()
            return True
        reward_line = self.order_line.filtered(lambda x: x.generated_from_line_id == product_line)
        if reward_line.coupon_program_id.reward_shipping_free == 'yes':
            #reward_line.with_context(noreward=True).write({'price_unit': reward_line.price_unit + (-delivery_charge_line.price_unit)})
            if not self.order_line.filtered(lambda x: x.generated_from_line_id == reward_line):
                vals = {
                    'product_id': self.env.ref('website_sale_coupon.product_product_reward').id,
                    'name': "Free Shipping",
                    'product_uom_qty': 1,
                    'price_unit': -delivery_charge_line.price_unit,
                    'order_id': self.id,
                    'coupon_program_id': reward_line.coupon_program_id.id,
                    'generated_from_line_id': reward_line.id,
                    'coupon_id': coupon_code
                }
                reward_line.with_context(noreward=True).create(vals)

    @api.multi
    def apply_immediately_reward(self):
        for order in self.filtered(lambda x: x.order_line is not False):
            programs = order._search_reward_programs([('program_type', '=', 'apply_immediately'), ('state', '=', 'opened')])
            if programs:
                self.process_rewards(programs, False)
            for order_line in [x for x in order.order_line if not (x.coupon_program_id or x.generated_from_line_id)]:
                order_line.apply_immediately_reward()
            self._check_current_reward_applicability([('program_type', '=', 'apply_immediately'), ('state', '=', 'opened')])
            self._check_current_reward_applicability([('program_type', '=', 'public_unique_code'), ('state', '=', 'opened')])
            self._check_current_reward_applicability([('program_type', '=', 'generated_coupon'), ('state', '=', 'opened')])
            self._check_for_free_shipping(False)

    @api.multi
    def apply_coupon_reward(self, coupon_code):
        program = self.env['sale.couponprogram'].search([('program_code', '=', coupon_code), ('state', '=', 'opened')], limit=1)
        if not program:
            coupon_obj = self.env['sale.coupon'].search([('coupon_code', '=', coupon_code), ('program_id.state', '=', 'opened')], limit=1)
            if not coupon_obj:
                return {'error': _('Coupon %s is invalid.') % (coupon_code)}
            if coupon_obj.state == 'used':
                return {'error': _('Coupon %s has been used.') % (coupon_code)}
            program = coupon_obj.program_id
        if program.check_is_program_expired(coupon_code):
            return {'error': _('Code %s has been expired') % (coupon_code)}
        if program.check_is_program_closed():
            return {'error': _('Program has been closed')}
        if program.program_type != 'apply_immediately':
            if program.purchase_type == 'amount' and ((self.amount_total >= program.minimum_amount and program.reward_tax == 'tax_excluded') or
                                                     (self.amount_untaxed >= program.minimum_amount and program.reward_tax == 'tax_excluded')):
                reward_product_id = self.env.ref('website_sale_coupon.product_product_reward')
                reward_line = self.order_line.filtered(lambda x: x.generated_from_line_id.id is False and x.product_id == reward_product_id)
                if reward_line:
                    return {'error': _('Code %s is already applied') % (coupon_code)}
                else:
                    self.process_rewards(program, coupon_code)
            if program.purchase_type == 'product':
                for line in self.order_line.filtered(lambda x: x.product_id == program.product_id and x.product_uom_qty >= program.product_quantity):
                    reward_line = self.order_line.filtered(lambda x: x.generated_from_line_id == line)
                    if reward_line:
                        return {'error': _('Code %s is already applied') % (coupon_code)}
                    else:
                        line.process_rewards(program, coupon_code)
            if program.purchase_type == 'category':
                for line in self.order_line.filtered(lambda x: x.product_id.categ_id == program.product_category_id and x.product_uom_qty >= program.product_quantity):
                    reward_line = self.order_line.filtered(lambda x: x.generated_from_line_id == line)
                    if reward_line:
                        return {'error': _('Code %s is already applied') % (coupon_code)}
                    else:
                        line.process_rewards(program, coupon_code)
            self._check_for_free_shipping(coupon_code)
        return {'update_price': True}

    @api.multi
    def process_rewards(self, programs, coupon_code):
        for program in programs:
            getattr(self, '_process_reward_' + program.reward_type)(program, coupon_code)

    def _process_reward_product(self, program, coupon_code):
        product_lines = self.order_line.filtered(lambda x: x.product_id == program.reward_product_product_id)
        vals = self.order_line.product_id_change(self.pricelist_id.id, program.reward_product_product_id.id, program.reward_quantity,
                                                 uom=program.reward_product_uom_id.id)['value']
        if not product_lines:
            vals['product_id'] = program.reward_product_product_id.id
            vals['product_uom_qty'] = program.reward_quantity
            vals['order_id'] = self.id
            vals['coupon_id'] = coupon_code
            line = self.order_line.with_context(noreward=True).create(vals)
        else:
            line = product_lines[0]
            if line.product_uom_qty < program.reward_quantity:
                line.with_context(noreward=True).write({'product_uom_qty': program.reward_quantity})
        self._create_discount_reward(program, vals['price_unit'], coupon_code)

    def _process_reward_discount(self, program, coupon_code):
        if program.reward_discount_type == 'amount':
            discount_amount = program.reward_discount_amount
        elif program.reward_discount_type == 'percentage':
            if program.reward_discount_on == 'cart':
                reward_line = self.order_line.filtered(lambda x: x.generated_from_line_id.id is False and x.coupon_program_id == program)
                if reward_line:
                    discount_amount = ((self.amount_total - (reward_line.price_unit)) * (program.reward_discount_percentage / 100))
                else:
                    discount_amount = self.amount_total * (program.reward_discount_percentage / 100)
            elif program.reward_discount_on == 'cheapest_product':
                    unit_prices = [x.price_unit for x in self.order_line if x.coupon_program_id.id is False]
                    discount_amount = (min(unit_prices) * (program.reward_discount_percentage) / 100)
            elif program.reward_discount_on == 'specific_product':
                discount_amount = sum([x.price_unit * (program.reward_discount_percentage / 100) for x in self.order_line if x.product_id == program.reward_discount_on_product_id])
        self._create_discount_reward(program, discount_amount, coupon_code)

    def _create_discount_reward(self, program, discount_amount, coupon_code):
        print "<<<<<<<<<<>.....ef", discount_amount
        reward_product_id = self.env.ref('website_sale_coupon.product_product_reward')
        reward_lines = self.order_line.filtered(lambda x: x.generated_from_line_id.id is False and x.product_id.id == reward_product_id.id and x.coupon_program_id == program)
        if discount_amount <= 0 and reward_lines:
            reward_lines.unlink()
        elif discount_amount > 0 and reward_lines:
            # for reward_line in reward_lines:
                # discount_amount += (-1) * reward_line.price_unit
            reward_lines.with_context(noreward=True).write({'price_unit': -discount_amount})
        elif discount_amount > 0 and not reward_lines:
            desc = "Reward on amount"
            if coupon_code:
                desc = desc + " using code " + coupon_code
            vals = {
                'product_id': reward_product_id.id,
                'name': desc,
                'product_uom_qty': program.reward_quantity,
                'price_unit': -discount_amount,
                'order_id': self.id,
                'coupon_program_id': program.id,
                'generated_from_line_id': False,
                'coupon_id': coupon_code
            }
            self.order_line.with_context(noreward=True).create(vals)
            if coupon_code:
                coupon_obj = self.env['sale.coupon'].search([('coupon_code', '=', coupon_code)])
                if coupon_obj:
                    coupon_obj.state = 'used'
                    #coupon_obj.order_line_id = False
                    coupon_obj.nbr_used = coupon_obj.nbr_used + 1
                    coupon_obj.reward_name = desc

    @api.multi
    def open_apply_coupon_wizard(self):
        return {
            'type': 'ir.actions.act_window',
            'name': "Enter coupon code",
            'res_model': 'sale.get.coupon',
            'view_mode': 'form',
            'views': [(False, 'form')],
            'target': 'new',
        }


class ProductTemplate(models.Model):
    _inherit = "product.template"

    is_delivery_chargeble = fields.Boolean("Delivery chargeble")


class GenerateManualCoupon(models.TransientModel):
    _name = 'sale.manual.coupon'

    nbr_coupons = fields.Integer("Number of coupons")

    @api.multi
    def generate_coupon(self):
        program_id = self.env['sale.couponprogram'].browse(self._context.get('active_id'))
        sale_coupon = self.env['sale.coupon']
        for count in range(0, self.nbr_coupons):
            sale_coupon.create({'program_id': program_id.id, 'nbr_uses': 1})


class GetCouponCode(models.TransientModel):
    _name = 'sale.get.coupon'

    textbox_coupon_code = fields.Char("Coupon", required=True)

    @api.multi
    def process_coupon(self):
        sale_order_id = self.env['sale.order'].browse(self._context.get('active_ids'))
        coupon_applied_satus = sale_order_id.apply_coupon_reward(self.textbox_coupon_code)
        if coupon_applied_satus.get('error'):
            raise UserError(_(coupon_applied_satus.get('error')))
