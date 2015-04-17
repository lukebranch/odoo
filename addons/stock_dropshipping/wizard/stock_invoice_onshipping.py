# -*- coding: utf-8 -*-

from openerp import api, fields, models
from openerp.tools.translate import _

class StockInvoiceOnshipping(models.TransientModel):
    _inherit = "stock.invoice.onshipping"

    @api.model
    def _get_journal_type(self):
        context = self.env.context
        res_ids = context and context.get('active_ids', [])
        Picking = self.env['stock.picking']
        pickings = Picking.browse(res_ids)
        pick = pickings and pickings[0]
        src_usage = pick.move_lines[0].location_id.usage
        dest_usage = pick.move_lines[0].location_dest_id.usage
        if src_usage == 'supplier' and dest_usage == 'customer':
            pick_purchase = pick.move_lines and pick.move_lines[0].purchase_line_id and pick.move_lines[0].purchase_line_id.order_id.invoice_method == 'picking'
            if pick_purchase:
                return 'purchase'
            else:
                return 'sale'
        else:
            return super(StockInvoiceOnshipping, self)._get_journal_type()

    journal_type = fields.Selection([('purchase_refund', 'Refund Purchase'), ('purchase', 'Create Supplier Invoice'),
                                     ('sale_refund', 'Refund Sale'), ('sale', 'Create Customer Invoice')], 'Journal Type', default=_get_journal_type, readonly=True)
