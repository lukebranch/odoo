from dateutil.relativedelta import relativedelta
import datetime
import time

from openerp import api, fields, models
from openerp.addons.decimal_precision import decimal_precision as dp
from openerp.tools.translate import _


class account_analytic_invoice_line(models.Model):

    _name = 'account.analytic.invoice.line'
    _inherit = 'account.analytic.invoice.line'

    actual_quantity = fields.Float('Actual Quantity', help="If the real quantity is higher than the prepaid quantity, the real quantity will be invoiced")
    discount = fields.Float('Discount (%)', digits_compute=dp.get_precision('Discount'))

    @api.multi
    def _amount_line(self, prop, unknow_none, unknow_dict):
        res = {}
        for line in self:
            res[line.id] = line.quantity * line.price_unit * (100.0 - line.discount) / 100.0
            if line.analytic_account_id.pricelist_id:
                cur = line.analytic_account_id.pricelist_id.currency_id
                res[line.id] = cur.round(res[line.id])
        return res

    @api.multi
    def product_id_change(self, product, uom_id, qty=0, name='', partner_id=False, price_unit=False, pricelist_id=False, company_id=None):
        res_final = super(account_analytic_invoice_line, self).product_id_change(product, uom_id, qty, name, partner_id, price_unit, pricelist_id, company_id)
        res = self.env['product.product'].browse(product)
        res_final['domain'] = {'uom_id': [('category_id', '=', res.uom_id.category_id.id)]}
        return res_final

    @api.multi
    def product_uom_change(self, product, uom_id, qty=0, name='', partner_id=False, pricelist_id=False):
        if not uom_id:
            return {'value': {'price_unit': 0.0, 'uom_id': uom_id or False}}
        return self.product_id_change(product, uom_id=uom_id, qty=qty, name=name, partner_id=partner_id, pricelist_id=pricelist_id)


class account_analytic_account(models.Model):

    _name = 'account.analytic.account'
    _inherit = 'account.analytic.account'

    def _get_contract_type_selection(self):
        return [("regular", "Regular"), ("prepaid", "Prepaid Support Hours"), ("subscription", "Subscription")]

    contract_type = fields.Selection(lambda s: s._get_contract_type_selection(), "Contract Type", help="Type of Contract", required=True, default="regular")
    recurring_total = fields.Float(compute='_get_recurring_price', string="Recurring Price", store=True, track_visibility='onchange')
    # Fields that only matters on template
    close_reason_id = fields.Many2one("account.analytic.close.reason", "Close Reason")

    @api.depends('recurring_invoice_line_ids', 'recurring_invoice_line_ids.product_id', 'recurring_invoice_line_ids.quantity',
                 'recurring_invoice_line_ids.actual_quantity', 'recurring_invoice_line_ids.uom_id', 'recurring_invoice_line_ids.price_unit',
                 'recurring_invoice_line_ids.price_subtotal')
    def _get_recurring_price(self):
        for account in self:
            account.recurring_total = sum(line.price_subtotal for line in account.recurring_invoice_line_ids)

    @api.multi
    def on_change_template(self, template_id, date_start=False):
        res = super(account_analytic_account, self).on_change_template(template_id, date_start)
        if template_id:
            template = self.browse(template_id)
            res['value']['contract_type'] = template.contract_type
            if template.contract_type == 'subscription':
                res['value']['date'] = False
            elif template.recurring_rule_type and template.recurring_interval:
                periods = {'daily': 'days', 'weekly': 'weeks', 'monthly': 'months', 'yearly': 'years'}
                contract_period = relativedelta(**{periods[template.recurring_rule_type]: template.recurring_interval})
                res['value']['date'] = datetime.datetime.strftime(datetime.date.today() + contract_period, openerp.tools.DEFAULT_SERVER_DATE_FORMAT)
        return res

    @api.model
    def _prepare_invoice_data(self, contract):
        invoice = super(account_analytic_account, self)._prepare_invoice_data(contract)
        next_date = datetime.datetime.strptime(contract.recurring_next_date, "%Y-%m-%d")
        periods = {'daily': 'days', 'weekly': 'weeks', 'monthly': 'months', 'yearly': 'years'}
        invoicing_period = relativedelta(**{periods[contract.recurring_rule_type]: contract.recurring_interval})
        new_date = next_date + invoicing_period

        invoice['comment'] = _("This invoice covers the following period: %s - %s") % (next_date.date(), new_date.date())

        return invoice

    @api.model
    def _prepare_invoice_lines(self, contract, fiscal_position_id):
        invoice_lines = super(account_analytic_account, self)._prepare_invoice_lines(contract, fiscal_position_id)
        for invoice_line, line in zip(invoice_lines, contract.recurring_invoice_line_ids):
            invoice_line[2]['discount'] = line.discount
            invoice_line[2]['quantity'] = max(line.quantity, line.actual_quantity)
        return invoice_lines

    @api.multi
    def prepare_renewal_order(self):
        self.ensure_one()
        order_lines = []
        order_sequence = self.env['ir.sequence'].search([('code', '=', 'sale.order')])
        for line in self.recurring_invoice_line_ids:
            order_lines.append((0, 0, {
                'product_id': line.product_id.id,
                'name': line.product_id.name_template,
                'description': line.name,
                'product_uom': line.uom_id.id,
                'product_uom_qty': line.quantity,
            }))
        order = {
            'name': order_sequence.next_by_id() + ' - ' + self.name + ' Renewal',
            'pricelist_id': self.pricelist_id.id,
            'partner_id': self.partner_id.id,
            'currency_id': self.pricelist_id.currency_id.id,
            'order_line': order_lines,
            'project_id': self.id,
            'update_contract': True,
        }
        order_id = self.env['sale.order'].create(order)
        return {
            "type": "ir.actions.act_window",
            "res_model": "sale.order",
            "views": [[False, "form"]],
            "res_id": order_id.id,
        }

        # not necessary once field recurring_invoices is removed
        @api.onchange('contract_type')
        def set_recurring_invoices(self):
            self.recurring_invoices = self.contract_type == 'subscription'


class AccountAnalyticCloseReason(models.Model):
    _name = "account.analytic.close.reason"
    _order = "sequence, id"

    name = fields.Char('Name', required=True)
    sequence = fields.Integer('Sequence', default=10)
