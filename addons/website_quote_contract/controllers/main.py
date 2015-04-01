from openerp.addons.web import http
from openerp.addons.web.http import request
from openerp.addons.website_quote.controllers.main import sale_quote
from openerp.tools.translate import _


class sale_quote_contract(sale_quote):
    @http.route([
        "/quote/<int:order_id>",
        "/quote/<int:order_id>/<token>"
    ], type='http', auth="public", website=True)
    def view(self, order_id, pdf=None, token=None, message=False, **post):
        response = super(sale_quote_contract, self).view(order_id, pdf, token, message, **post)
        if 'quotation' in response.qcontext:  # check if token identification was ok in super
            order = response.qcontext['quotation']
            recurring_products = True in [line.product_id.recurring_invoice for line in order.sudo().order_line]
            tx_type = 'form_save' if recurring_products else 'form'
            # re-render the payment buttons with the proper tx_type if recurring products
            if 'acquirers' in response.qcontext and tx_type != 'form':
                render_ctx = dict(request.context, submit_class='btn btn-primary', submit_txt=_('Pay & Confirm'))
                for acquirer in response.qcontext['acquirers']:
                    acquirer.button = acquirer.with_context(render_ctx).render(
                        order.name,
                        order.amount_total,
                        order.pricelist_id.currency_id.id,
                        partner_id=order.partner_id.id,
                        tx_values={
                            'return_url': '/quote/' + str(order_id) + '/confirm',
                            'type': tx_type,
                            'alias_usage': _('If we store your payment information on our server, subscription payments will be made automatically.')
                        })[0]
                    response.qcontext['recurring_products'] = recurring_products
        return response

    # note dbo: website_sale code
    @http.route(['/quote/<int:order_id>/transaction/<int:acquirer_id>'], type='json', auth="public", website=True)
    def payment_transaction(self, acquirer_id, order_id):
        """Let's use inheritance to change the tx type if there are recurring products in the order
        """
        response = super(sale_quote_contract, self).payment_transaction(acquirer_id, order_id)
        if isinstance(response, int):
            tx_id = response
            tx = request.env['payment.transaction'].sudo().browse(tx_id)
            order = request.env['sale.order'].sudo().browse(order_id)
            if True in [line.product_id.recurring_invoice for line in order.order_line]:
                tx.type = 'form_save'
        return response
