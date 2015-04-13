# -*- coding: utf-8 -*-

from openerp import http, _
from openerp.http import request
from openerp.addons.website_event.controllers.main import website_event
from openerp.addons.website_sale.controllers.main import get_pricelist


class website_event(website_event):

    @http.route(['/event/<model("event.event"):event>/register'], type='http', auth="public", website=True)
    def event_register(self, event, **post):
        pricelist_id = int(get_pricelist())
        values = {
            'event': event.with_context(pricelist=pricelist_id),
            'main_object': event.with_context(pricelist=pricelist_id),
            'range': range,
        }
        return request.website.render("website_event.event_description_full", values)

    def _process_tickets_details(self, data):
        ticket_post = {}
        for key, value in data.iteritems():
            if not key.startswith('nb_register') or not '-' in key:
                continue
            items = key.split('-')
            if len(items) < 2:
                continue
            ticket_post[int(items[1])] = int(value)
        tickets = request.env['event.event.ticket'].browse(ticket_post.keys())
        return [{'id': ticket.id, 'name': ticket.name, 'quantity': ticket_post[ticket.id], 'price': ticket.price} for ticket in tickets if ticket_post[ticket.id]]

    @http.route(['/event/<model("event.event"):event>/registration/confirm'], type='http', auth="public", methods=['POST'], website=True)
    def registration_confirm(self, event, **post):
        order = request.website.sale_get_order(force_create=1)

        registrations = self._process_registration_details(post)
        for registration in registrations:
            ticket = request.env['event.event.ticket'].sudo().browse(int(registration['ticket_id']))
            order.with_context(event_ticket_id=ticket.id)._cart_update(product_id=ticket.product_id.id, add_qty=1, registration_data=[registration])

        return request.redirect("/shop/checkout")

    def _add_event(self, event_name="New Event", context={}, **kwargs):
        try:
            res_id = request.env.ref('event_sale.product_product_event').id
            context['default_event_ticket_ids'] = [[0, 0, {
                'name': _('Subscription'),
                'product_id': res_id,
                'deadline': False,
                'seats_max': 1000,
                'price': 0,
            }]]
        except ValueError:
            pass
        return super(website_event, self)._add_event(event_name, context, **kwargs)
