# -*- coding: utf-8 -*-

from openerp import http
from openerp.http import request


class PickingWaveReport(http.Controller):
    @http.route('/report/stock_picking_wave.report_pickingwave/<ids>', type='http', auth='user',
                website=True)
    def report_picking_wave(self):
        picking_wave_obj = self.env["stock.picking.wave"]
        wave = picking_wave_obj.browse(self.id)
        docargs = {
            'docs': wave.picking_ids,
        }
        return request.registry['report'].render(self, 'stock.report_picking', docargs)
