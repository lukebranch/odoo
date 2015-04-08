# -*- coding: utf-8 -*-
from openerp import api, fields, models
from openerp.http import request

class IrUiView(models.Model):

    _inherit = "ir.ui.view"

    @api.model
    def _prepare_qcontext(self):
        qcontext = super(IrUiView, self)._prepare_qcontext()
        if request and getattr(request, 'website_enabled', False):
            if request.website.channel_id:
                qcontext['website_livechat_url'] = self.env['ir.config_parameter'].get_param('web.base.url')
                qcontext['website_livechat_dbname'] = self.env.cr.dbname
                qcontext['website_livechat_channel'] = request.website.channel_id.id
        return qcontext

