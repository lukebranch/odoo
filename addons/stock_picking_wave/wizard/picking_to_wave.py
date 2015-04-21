# -*- coding: utf-8 -*-

from openerp import api, fields, models
from openerp.tools.translate import _

class StockPickingToWave(models.TransientModel):
    _name = 'stock.picking.to.wave'
    _description = 'Add pickings to a picking wave'
    wave_id = fields.Many2one('stock.picking.wave', 'Picking Wave', required=True)

    def attach_pickings(self):
        #use active_ids to add picking line to the selected wave
        wave_id = self.wave_id.id
        return self.env['stock.picking'].write({'wave_id': wave_id})
