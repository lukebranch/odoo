# -*- coding: utf-8 -*-
import logging
import openerp
from openerp import http

_logger = logging.getLogger(__name__)

data = ''

class PosScreen(openerp.addons.web.controllers.main.Home):


    @http.route('/screen/get_data', type='json', auth='none', website=True)
    def screen(self):
        return data

    @http.route('/screen/set_data', type='json', auth='none', website=True)
    def set_data(self, ** kwargs):
        print kwargs['data']
        if kwargs['data']:
            data = kwargs['data']
