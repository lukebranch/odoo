# -*- coding: utf-8 -*-
from openerp import api, fields, models


class DeliveryCarrier(models.Model):
    _name = 'delivery.carrier'
    _inherit = ['delivery.carrier', 'website.published.mixin']

    website_description = fields.Text('Description for Online Quotations')
    website_published = fields.Boolean('Visible in Website', default=True, copy=False)
