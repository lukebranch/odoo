from openerp import models, api


class AccountUnreconcile(models.TransientModel):
    _name = "account.unreconcile"
    _description = "Account Unreconcile"

    @api.multi
    def trans_unrec(self):
        context = dict(self.env.context or {})
        if context.get('active_ids'):
            self.env['account.move.line'].browse(context.get('active_ids')).remove_move_reconcile()
        return {'type': 'ir.actions.act_window_close'}
