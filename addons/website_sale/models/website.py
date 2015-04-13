from openerp import api, fields, models
from openerp.http import request


class Website(models.Model):
    _inherit = 'website'

    pricelist_id = fields.Many2one('product.pricelist', related='user_id.partner_id.property_product_pricelist', string='Default Pricelist')
    currency_id = fields.Many2one('res.currency', related='pricelist_id.currency_id', string='Default Currency')

    @api.multi
    def sale_product_domain(self):
        return [("sale_ok", "=", True)]

    def sale_get_order(self, force_create=False, code=None, update_pricelist=None):
        SaleOrder = self.env['sale.order'].sudo()
        sale_order_id = request.session.get('sale_order_id')
        sale_order = None
        # create so if needed
        if not sale_order_id and (force_create or code):
            # TODO cache partner_id session
            partner = self.env.user.sudo().partner_id

            for w in self:
                values = {
                    'user_id': w.user_id.id,
                    'partner_id': partner.id,
                    'pricelist_id': partner.property_product_pricelist.id,
                    'team_id': self.env.ref('website.salesteam_website_sales').id,
                }
                sale_order = SaleOrder.create(values)
                values = SaleOrder.onchange_partner_id(part=partner.id)['value']
                sale_order.write(values)
                request.session['sale_order_id'] = sale_order.id
        if sale_order_id:
            # TODO cache partner_id session
            partner = self.env.user.sudo().partner_id

            sale_order = SaleOrder.browse(sale_order_id)
            if not sale_order.exists():
                request.session['sale_order_id'] = None
                return None

            # check for change of pricelist with a coupon
            if code and code != sale_order.pricelist_id.code:
                pricelist = self.env['product.pricelist'].sudo().search([('code', '=', code)], limit=1)
                request.session['sale_order_code_pricelist_id'] = pricelist.id
                update_pricelist = True

            pricelist_id = request.session.get('sale_order_code_pricelist_id') or partner.property_product_pricelist.id

            # check for change of partner_id ie after signup
            if sale_order.partner_id.id != partner.id and request.website.partner_id.id != partner.id:
                flag_pricelist = False
                if pricelist_id != sale_order.pricelist_id.id:
                    flag_pricelist = True
                fiscal_position = sale_order.fiscal_position and sale_order.fiscal_position.id or False

                values = sale_order.onchange_partner_id(part=partner.id)['value']
                if values.get('fiscal_position'):
                    order_lines = map(int, sale_order.order_line)
                    values.update(SaleOrder.onchange_fiscal_position([],
                                                                     values['fiscal_position'], [[6, 0, order_lines]])['value'])

                values['partner_id'] = partner.id
                sale_order.write(values)

                if flag_pricelist or values.get('fiscal_position') != fiscal_position:
                    update_pricelist = True

            # update the pricelist
            if update_pricelist:
                values = {'pricelist_id': pricelist_id}
                values.update(sale_order.onchange_pricelist_id(pricelist_id, None)['value'])
                sale_order.write(values)
                for line in sale_order.order_line:
                    sale_order._cart_update(product_id=line.product_id.id, line_id=line.id, add_qty=0)

            # update browse record
            if (code and code != sale_order.pricelist_id.code) or sale_order.partner_id.id != partner.id:
                sale_order = SaleOrder.browse(sale_order.id)
        return sale_order

    def sale_get_transaction(self):
        tx_id = request.session.get('sale_transaction_id')
        if tx_id:
            tx = self.env['payment.transaction'].sudo().search([('id', '=', tx_id), ('state', 'not in', ['cancel'])], limit=1)
            if tx:
                return tx
            else:
                request.session['sale_transaction_id'] = False
        return False

    def sale_reset(self):
        request.session.update({
            'sale_order_id': False,
            'sale_transaction_id': False,
            'sale_order_code_pricelist_id': False,
        })
