##############################################################################
#    
#    OpenERP, Open Source Management Solution
#    Copyright (C) 
#    2004-2010 Tiny SPRL (<http://tiny.be>). 
#    2009-2010 Veritos (http://veritos.nl).
#    All Rights Reserved
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.     
#
##############################################################################

from openerp.osv import osv, fields
from tools.translate import _
from openerp import api


class aml_creator_mixin(osv.AbstractModel):
    _inherit = "aml.creator.mixin"

    @api.v8
    def get_aml_dict(self):
        res = super(aml_creator_mixin,self).get_aml_dict()
        if self.company_id.anglo_saxon_accounting:
            if self.product_id and self.product_id.valuation == 'real_time' and self.product_id.type != 'service':
                mixin_type = self.get_mixin_type()
                if mixin_type in ('out_invoice', 'out_refund'):
                    #extend with cost of sale lines
                    res.extend(self._anglo_saxon_sale_move_lines())
                elif mixin_type in ('in_invoice', 'in_refund'):
                    #modify price with product cost and extend with a line containing the price difference
                    res = self._anglo_saxon_purchase_move_lines(res)
        return res

    @api.v8
    def _anglo_saxon_sale_move_lines(self):
        """Return the additional move lines for sales and sale refunds."""
        # debit account dacc will be the output account
        # first check the product, if empty check the category
        dacc = self.product_id.property_stock_account_output.id or self.product_id.categ_id.property_stock_account_output_categ.id
        # in both cases the credit account cacc will be the expense account
        # first check the product, if empty check the category
        cacc = self.product_id.property_account_expense.id or self.product_id.categ_id.property_account_expense_categ.id
        if dacc and cacc:
            #for sales, we always take the price_unit of the move -whatever the costing method of the product- since we want to clear the stock output account
            price_unit = self.move_id and self.move_id.price_unit or self.product_id.standard_price
            product_cost = self.product_id.uom_id._compute_price(price_unit * self.quantity, self.uos_id.id)
            return [
                {
                    'name': self.name[:64],
                    'quantity': self.quantity,
                    'debit': product_cost > 0 and product_cost,
                    'credit': product_cost < 0 and -product_cost,
                    'account_id': dacc,
                    'product_id': self.product_id.id,
                    'product_uom_id': self.uos_id.id,
                    'account_analytic_id': False,
                },
                {
                    'name': self.name[:64],
                    'quantity': self.quantity,
                    'debit': -product_cost > 0 and product_cost,
                    'credit': -product_cost < 0 and -product_cost,
                    'account_id': cacc,
                    'product_id': self.product_id.id,
                    'product_uom_id': self.uos_id.id,
                    'account_analytic_id': False,
                }]
        return []

    @api.model
    def _anglo_saxon_purchase_move_lines(self, res):
        """Modify price with product cost and extend with a line containing the price difference"""
        price_unit = self.product_id.standard_price
        product_cost = self.product_id.uom_id._compute_price(price_unit * self.quantity, self.uos_id.id)
        if self.product_id.cost_method != 'standard' and self.purchase_line_id:
            #For purchases, if the costing method is average or real price we have to use the cost price from the PO because we want to clear the stock input account.
            valuation_stock_move = self.env['stock.move'].search(self.cr, self.uid, [('purchase_line_id', '=', self.purchase_line_id.id)], limit=1, context=self._context)
            if valuation_stock_move:
                product_cost = valuation_stock_move.price_unit
        acc = self.product_id.property_account_creditor_price_difference.id or self.product_id.categ_id.property_account_creditor_price_difference_categ.id
        if product_cost != res[0]['price'] and acc:
            old_price = res[0]['price']
            #modify with product cost
            res[0].update({'price': product_cost})
            #extend with price difference
            new_line = res[0].copy()
            new_line.update({'price': old_price - product_cost, 'account_id': acc})
            res.extend([new_line])
        return res


class account_invoice_line(osv.osv):
    _inherit = "account.invoice.line"

    _columns = {
        'move_id': fields.many2one('stock.move', string="Move line", help="If the invoice was generated from a stock.picking, reference to the related move line."),
    }

    @api.v8
    def get_invoice_line_account(self, product, fpos):
        if self.company_id.anglo_saxon_accounting and self.invoice_id.type in ('in_invoice', 'in_refund'):
            accounts = product.get_product_accounts(fpos)
            if self.invoice_id.type == 'in_invoice':
                return accounts['stock_input']
            return accounts['stock_ouput']
        return super(account_invoice_line, self).get_invoice_line_account(product, fpos)


class account_invoice(osv.osv):
    _inherit = "account.invoice"

    def _prepare_refund(self, cr, uid, invoice, date_invoice=None, date=None, description=None, journal_id=None, context=None):
        invoice_data = super(account_invoice, self)._prepare_refund(cr, uid, invoice, date, date,
                                                                    description, journal_id, context=context)
        if invoice.type == 'in_invoice':
            fiscal_position = self.pool.get('account.fiscal.position')
            for dummy, dummy, line_dict in invoice_data['invoice_line']:
                if line_dict.get('product_id'):
                    product = self.pool.get('product.product').browse(cr, uid, line_dict['product_id'], context=context)
                    counterpart_acct_id = product.property_stock_account_output and \
                            product.property_stock_account_output.id
                    if not counterpart_acct_id:
                        counterpart_acct_id = product.categ_id.property_stock_account_output_categ and \
                                product.categ_id.property_stock_account_output_categ.id
                    if counterpart_acct_id:
                        fpos = invoice.fiscal_position or False
                        line_dict['account_id'] = fiscal_position.map_account(cr, uid,
                                                                              fpos,
                                                                              counterpart_acct_id)
        return invoice_data

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
