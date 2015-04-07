# -*- coding: utf-8 -*-

from openerp.exceptions import UserError
from openerp import api, models, fields, _

class WizardPrice(models.Model):
    _name = "wizard.price"
    _description = "Compute price wizard"

    info_field = fields.Text("Info", readonly=True)
    real_time_accounting = fields.Boolean("Generate accounting entries when real-time")
    recursive = fields.Boolean("Change prices of child BoMs too")

    @api.model
    def default_get(self, fields):
        res = super(WizardPrice, self).default_get(fields)
        ctx = dict(self.env.context)
        rec_id = ctx.get('active_id')
        assert rec_id, _('Active ID is not set in Context.')
        Product = self.env['product.template'].browse(rec_id)
        ctx['no_update'] = True
        res['info_field'] = str(Product.with_context(ctx).compute_standard_price())
        return res

    @api.one
    def compute_from_bom(self):
        ctx = dict(self.env.context)
        model = ctx.get('active_model')
        if model != 'product.template':
            raise UserError(_('This wizard is build for product templates, while you are currently running it from a product variant.'))
        rec_id = ctx.get('active_id')
        assert rec_id, _('Active ID is not set in Context.')
        ctx['no_update'] = False
        Product = self.env['product.template'].browse(rec_id)
        prod = Product.browse(rec_id)
        Product.with_context(ctx).compute_standard_price(recursive=self.recursive, real_time_accounting=self.real_time_accounting)
