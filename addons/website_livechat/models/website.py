# -*- coding: utf-8 -*-
from openerp import api, fields, models

class Website(models.Model):

    _inherit = "website"

    channel_id = fields.Many2one('im_livechat.channel', string='Live Chat Channel')


class WebsiteConfigSettings(models.TransientModel):

    _inherit = 'website.config.settings'

    channel_id = fields.Many2one('im_livechat.channel', string='Live Chat Channel', related='website_id.channel_id')


