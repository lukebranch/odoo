# -*- coding: utf-8 -*-

import werkzeug

from openerp import fields, http, _
from openerp.http import request


class SaleQuote(http.Controller):
    @http.route([
        "/quote/<int:order_id>",
        "/quote/<int:order_id>/<token>"
    ], type='http', auth="public", website=True)
    def view(self, order_id, pdf=None, token=None, message=False, **post):
        # use SUPERUSER_ID allow to access/view order for public user
        # only if he knows the private token
        Order = request.env['sale.order']
        if token:
            sale_order = Order.sudo().browse(order_id)
        else:
            sale_order = Order.browse(order_id)
        now = fields.Date.from_string(fields.Date.today())
        action_id = request.env.ref('sale.action_quotations').id
        if token:
            if token != sale_order.access_token:
                return request.website.render('website.404')
            # Log only once a day
            if request.session.get('view_quote', False) != now:
                request.session['view_quote'] = now
                body = _('Quotation viewed by customer')
                self.__message_post(body, order_id, type='comment')
        days = 0
        if sale_order.validity_date:
            days = (fields.Datetime.from_string(sale_order.validity_date) - fields.Datetime.from_string(fields.Datetime.now())).days + 1
        if pdf:
            pdf = request.env['report'].sudo().get_pdf(sale_order, 'website_quote.report_quote')
            pdfhttpheaders = [('Content-Type', 'application/pdf'), ('Content-Length', len(pdf))]
            return request.make_response(pdf, headers=pdfhttpheaders)
        values = {
            'quotation': sale_order,
            'message': message and int(message) or False,
            'option': bool(sale_order.options.filtered(lambda x: not x.line_id)),
            'order_valid': (not sale_order.validity_date) or (now <= fields.Date.from_string(sale_order.validity_date)),
            'days_valid': max(days, 0),
            'action': action_id
        }
        return request.website.render('website_quote.so_quotation', values)

    @http.route(['/quote/accept'], type='json', auth="public", website=True)
    def accept(self, order_id, token=None, signer=None, sign=None, **post):
        order = request.env['sale.order'].sudo().browse(order_id)
        if token != order.access_token:
            return request.website.render('website.404')
        attachments = sign and [('signature.png', sign.decode('base64'))] or []
        order.signal_workflow('order_confirm')
        message = _('Order signed by %s') % (signer,)
        self.__message_post(message, order.id, type='comment', subtype='mt_comment', attachments=attachments)
        return True

    @http.route(['/quote/<int:order_id>/<token>/decline'], type='http', auth="public", website=True)
    def decline(self, order_id, token, **post):
        order = request.env['sale.order'].sudo().browse(order_id)
        if token != order.access_token:
            return request.website.render('website.404')
        order.action_cancel()
        message = post.get('decline_message')
        if message:
            self.__message_post(message, order_id, type='comment', subtype='mt_comment')
        return werkzeug.utils.redirect("/quote/%s/%s?message=2" % (order_id, token))

    @http.route(['/quote/<int:order_id>/<token>/post'], type='http', auth="public", website=True)
    def post(self, order_id, token, **post):
        # use SUPERUSER_ID allow to access/view order for public user
        order = request.env['sale.order'].sudo().browse(order_id)
        message = post.get('comment')
        if token != order.access_token:
            return request.website.render('website.404')
        if message:
            self.__message_post(message, order_id, type='comment', subtype='mt_comment')
        return werkzeug.utils.redirect("/quote/%s/%s?message=1" % (order_id, token))

    def __message_post(self, message, order_id, type='comment', subtype=False, attachments=[]):
        request.session.body = message
        User_sudo = request.env.user.sudo()
        if 'body' in request.session and request.session.body:
            request.env['sale.order'].browse(order_id).sudo().message_post(body=request.session.body, type=type,
                    subtype=subtype, author_id=User_sudo.partner_id.id, attachments=attachments)
            request.session.body = False
        return True

    @http.route(['/quote/update_line'], type='json', auth="public", website=True)
    def update(self, line_id, remove=False, unlink=False, order_id=None, token=None, **post):
        order = request.env['sale.order'].sudo().browse(int(order_id))
        if token != order.access_token:
            return request.website.render('website.404')
        if order.state not in ('draft', 'sent'):
            return False
        line_id = int(line_id)
        if unlink:
            request.env['sale.order.line'].browse(line_id).sudo().unlink()
            return False
        number = (remove and -1 or 1)
        order_line = request.env['sale.order.line'].sudo().browse(line_id)
        quantity = order_line.product_uom_qty + number
        order_line.write({'product_uom_qty': (quantity)})
        return [str(quantity), str(order.amount_total)]

    @http.route(["/quote/template/<model('sale.quote.template'):quote>"], type='http', auth="user", website=True)
    def template_view(self, quote, **post):
        values = {'template': quote}
        return request.website.render('website_quote.so_template', values)

    @http.route(["/quote/add_line/<int:option_id>/<int:order_id>/<token>"], type='http', auth="public", website=True)
    def add(self, option_id, order_id, token, **post):
        vals = {}
        order = request.env['sale.order'].sudo().browse(order_id)
        if token != order.access_token:
            return request.website.render('website.404')
        if order.state not in ['draft', 'sent']:
            return request.website.render('website.http_error', {'status_code': 'Forbidden', 'status_message': _('You cannot add options to a confirmed order.')})
        option = request.env['sale.order.option'].sudo().browse(option_id)

        result = request.env['sale.order.line'].browse(order_id).product_id_change(
            False, option.product_id.id, option.quantity, option.uom_id.id, option.quantity, option.uom_id.id,
            option.name, order.partner_id.id, False, True, fields.Date.today(),
            False, order.fiscal_position.id, True)
        vals = result.get('value', {})
        if 'tax_id' in vals:
            vals['tax_id'] = [(6, 0, vals['tax_id'])]

        vals.update({
            'price_unit': option.price_unit,
            'website_description': option.website_description,
            'name': option.name,
            'order_id': order.id,
            'product_id': option.product_id.id,
            'product_uos_qty': option.quantity,
            'product_uos': option.uom_id.id,
            'product_uom_qty': option.quantity,
            'product_uom': option.uom_id.id,
            'discount': option.discount,
        })
        order_line = request.env['sale.order.line'].sudo().create(vals)
        option.write({'line_id': order_line.id})
        return werkzeug.utils.redirect("/quote/%s/%s#pricing" % (order.id, token))
