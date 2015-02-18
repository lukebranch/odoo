# -*- encoding: utf-8 -*-

from datetime import datetime
from dateutil.relativedelta import relativedelta
from openerp import models, fields, api
import openerp.addons.decimal_precision as dp


class account_invoice(models.Model):
    _inherit = 'account.invoice'

    @api.multi
    def action_number(self):
        result = super(account_invoice, self).action_number()
        for inv in self:
            inv.invoice_line.asset_create()
        return result

    @api.model
    def line_get_convert(self, line, part, date):
        res = super(account_invoice, self).line_get_convert(line, part, date)
        res['asset_id'] = line.get('asset_id', False)
        return res


class account_invoice_line(models.Model):
    _inherit = 'account.invoice.line'

    asset_category_id = fields.Many2one('account.asset.category', string='Asset Category')
    asset_start_date = fields.Date(string='Asset End Date', compute='_get_asset_date', readonly=True, store=True)
    asset_end_date = fields.Date(string='Asset Start Date', compute='_get_asset_date', readonly=True, store=True)
    mrr = fields.Float(string='Monthly Recurring Revenue', compute='_get_mrr', store=True, readonly=True, digits=dp.get_precision('Account'))

    @api.one
    @api.depends('asset_category_id')
    def _get_mrr(self):
        # use MAT field to caculate MRR
        if self.asset_category_id:
            self.mrr = self.price_subtotal/(self.asset_category_id.method_period*self.asset_category_id.method_number)
            # mrr negative if supplier invoice
            if self.invoice_id.type in ['in_invoice', 'out_refund']:
                self.mrr = -self.mrr
        else:
            self.mrr = 0.

    @api.one
    @api.depends('asset_category_id')
    def _get_asset_date(self):
        if self.asset_category_id:
            self.asset_start_date = self.invoice_id.date_due
            months = self.asset_category_id.method_number * self.asset_category_id.method_period
            start_date = datetime.strptime(self.invoice_id.date_due, '%Y-%m-%d')
            end_date = start_date + relativedelta(months=months)
            self.asset_end_date = end_date.strftime('%Y-%m-%d')
        else:
            self.asset_start_date = False
            self.asset_end_date = False

    @api.one
    def asset_create(self):
        asset_obj = self.env['account.asset.asset']
        if self.asset_category_id and self.asset_category_id.method_number > 1:
            vals = {
                'name': self.name,
                'code': self.invoice_id.number or False,
                'category_id': self.asset_category_id.id,
                'value': self.price_subtotal,
                'partner_id': self.invoice_id.partner_id.id,
                'company_id': self.invoice_id.company_id.id,
                'currency_id': self.invoice_id.currency_id.id,
                'date': self.asset_start_date or self.invoice_id.date_invoice,
                'invoice_id': self.invoice_id.id,
            }
            changed_vals = asset_obj.onchange_category_id(vals['category_id'])
            vals.update(changed_vals['value'])
            asset = asset_obj.create(vals)
            if self.asset_category_id.open_asset:
                asset.validate()
        return True
