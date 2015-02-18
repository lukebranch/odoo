# -*- coding: utf-8 -*-
import logging
import werkzeug.utils

from openerp import http
from openerp.http import request
from openerp.addons.web.controllers.main import login_redirect, abort_and_redirect

_logger = logging.getLogger(__name__)


class PosKioskController(http.Controller):

    @http.route('/pos/screen/template/<int:config>', type='http', auth='user')
    def screen_template(self, config, **k):
        return request.env['pos.config'].browse(config).kiosk_template
