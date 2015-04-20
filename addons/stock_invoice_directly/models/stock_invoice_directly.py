# -*- coding: utf-8 -*-

from openerp import api, models
from openerp.tools.translate import _


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    @api.multi
    def do_transfer(self):
        """Launch Create invoice wizard if invoice state is To be Invoiced,
          after processing the picking.
        """
        context = self.env.context
        res = super(StockPicking, self).do_transfer()
        pick_ids = [p.id for p in self if p.invoice_state == '2binvoiced']
        if pick_ids:
            context = dict(context, active_model='stock.picking', active_ids=pick_ids)
            return {
                'name': _('Create Invoice'),
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'stock.invoice.onshipping',
                'type': 'ir.actions.act_window',
                'target': 'new',
                'context': context
            }
        return res
