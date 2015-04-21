# -*- coding: utf-8 -*-
from openerp import api, fields, models
from openerp.tools.translate import _
from openerp.exceptions import UserError

class StockPickingWave(models.Model):
    _inherit = "mail.thread"
    _name = "stock.picking.wave"
    _description = "Picking Wave"
    _order = "name desc"
    name = fields.Char('Picking Wave Name', default="/", required=True, help='Name of the picking wave', copy=False)
    user_id = fields.Many2one('res.users', 'Responsible', track_visibility='onchange', help='Person responsible for this wave')
    picking_ids = fields.One2many('stock.picking', 'wave_id', 'Pickings', help='List of picking associated to this wave')
    state = fields.Selection([('draft', 'Draft'), ('in_progress', 'Running'), ('done', 'Done'), ('cancel', 'Cancelled')], default="draft", string="State", required=True, copy=False)

    @api.multi
    def confirm_picking(self):
        picking = self.env['stock.picking'].search([('wave_id', 'in', self.ids)], limit=1)
        self.write({'state': 'in_progress'})
        return picking.action_assign()

    @api.multi
    def cancel_picking(self):
        picking = self.env['stock.picking'].search([('wave_id', 'in', self.ids)])
        picking.action_cancel()
        return self.write({'state': 'cancel'})

    @api.multi
    def print_picking(self):
        '''
        This function print the report for all picking_ids associated to the picking wave
        '''
        return self.env["report"].get_action(self, 'stock.report_picking')

    @api.model
    def create(self, vals):
        if vals.get('name', '/') == '/':
            vals['name'] = self.env['ir.sequence'].next_by_code('picking.wave') or '/'
        return super(StockPickingWave, self).create(vals)

    @api.multi
    def done(self):
        picking_todo = set()
        for wave in self:
            for picking in wave.picking_ids:
                if picking.state in ('cancel', 'done'):
                    continue
                if picking.state != 'assigned':
                    raise UserError(_('Some pickings are still waiting for goods. Please check or force their availability before setting this wave to done.'))
                message_body = "<b>%s:</b> %s <a href=#id=%s&view_type=form&model=stock.picking.wave>%s</a>" % (_("Transferred by"), _("Picking Wave"), wave.id, wave.name)
                picking.message_post(body=message_body)
                picking_todo.add(picking.id)
        if picking_todo:
            picking.action_done()
        return wave.write({'state': 'done'})

    def _track_subtype(self, init_values):
        print "...init_values...", init_values
        if 'state' in init_values and self.state != 'draft':
            return 'stock_picking_wave.state'
        return super(StockPickingWave, self)._track_subtype(init_values)


class StockPicking(models.Model):
    _inherit = "stock.picking"
    wave_id = fields.Many2one('stock.picking.wave', 'Picking Wave', states={'done': [('readonly', True)], 'cancel': [('readonly', True)]}, help='Picking wave associated to this picking')
