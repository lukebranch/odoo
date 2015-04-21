# -*- coding: utf-8 -*-

from openerp import api, fields, models
import openerp.addons.decimal_precision as dp
from openerp.tools.translate import _
import product
from openerp.exceptions import UserError


class StockLandedCost(models.Model):
    _name = 'stock.landed.cost'
    _description = 'Stock Landed Cost'
    _inherit = 'mail.thread'

    @api.depends('cost_lines', 'cost_lines.price_unit', 'cost_lines.cost_id')
    def _total_amount(self):
        for cost in self.cost_lines:
            self.amount_total += cost.price_unit

    def get_valuation_lines(self, picking_ids):
        Picking = self.env['stock.picking']
        lines = []
        if not self.picking_ids:
            return lines
        for picking in Picking.browse(picking_ids):
            for move in picking.move_lines:
                #it doesn't make sense to make a landed cost for a product that isn't set as being valuated in real time at real cost
                if move.product_id.valuation != 'real_time' or move.product_id.cost_method != 'real':
                    continue
                total_cost = 0.0
                total_qty = move.product_qty
                weight = move.product_id and move.product_id.weight * move.product_qty
                volume = move.product_id and move.product_id.volume * move.product_qty
                for quant in move.quant_ids:
                    total_cost += quant.cost
                vals = dict(product_id=move.product_id.id, move_id=move.id, quantity=move.product_uom_qty, former_cost=total_cost * total_qty, weight=weight, volume=volume)
                lines.append(vals)
        if not lines:
            raise UserError(_('The selected picking does not contain any move that would be impacted by landed costs. Landed costs are only possible for products configured in real time valuation with real price costing method. Please make sure it is the case, or you selected the correct picking'))
        return lines

    name = fields.Char(track_visibility='always', default=lambda self: self.env['ir.sequence'].next_by_code('stock.landed.cost'), readonly=True, copy=False)
    date = fields.Date(required=True, states={'done': [('readonly', True)]}, default=fields.Date.context_today, track_visibility='onchange', copy=False)
    picking_ids = fields.Many2many('stock.picking', string='Pickings', states={'done': [('readonly', True)]}, copy=False)
    cost_lines = fields.One2many('stock.landed.cost.lines', 'cost_id', 'Cost Lines', states={'done': [('readonly', True)]}, copy=True)
    valuation_adjustment_lines = fields.One2many('stock.valuation.adjustment.lines', 'cost_id', 'Valuation Adjustments', states={'done': [('readonly', True)]})
    description = fields.Text('Item Description', states={'done': [('readonly', True)]})
    amount_total = fields.Float(compute='_total_amount', string='Total', digits_compute=dp.get_precision('Account'), store=True,
                                track_visibility='always')
    state = fields.Selection([('draft', 'Draft'), ('done', 'Posted'), ('cancel', 'Cancelled')], default='draft', readonly=True, track_visibility='onchange', copy=False)
    account_move_id = fields.Many2one('account.move', 'Journal Entry', readonly=True, copy=False)
    account_journal_id = fields.Many2one('account.journal', 'Account Journal', required=True)

    def _create_accounting_entries(self, line, move_id, qty_out):
        Product = self.env['product.template']
        cost_product = line.cost_line_id and line.cost_line_id.product_id
        if not cost_product:
            return False
        accounts = Product.get_product_accounts(line.product_id.product_tmpl_id.id)
        debit_account_id = accounts['property_stock_valuation_account_id']
        already_out_account_id = accounts['stock_account_output']
        credit_account_id = line.cost_line_id.account_id.id or cost_product.property_account_expense.id or cost_product.categ_id.property_account_expense_categ.id

        if not credit_account_id:
            raise UserError(_('Please configure Stock Expense Account for product: %s.') % (cost_product.name))
        return self._create_account_move_line(line, move_id, credit_account_id, debit_account_id, qty_out, already_out_account_id)

    def _create_account_move_line(self, line, move_id, credit_account_id, debit_account_id, qty_out, already_out_account_id):
        """
        Generate the account.move.line values to track the landed cost.
        Afterwards, for the goods that are already out of stock, we should create the out moves
        """
        AccountMoveLine = self.env['account.move.line']
        AccountMoveLine.create({
            'name': line.name,
            'move_id': move_id.id,
            'product_id': line.product_id.id,
            'quantity': line.quantity,
            'debit': line.additional_landed_cost,
            'account_id': debit_account_id})
        AccountMoveLine.create({
            'name': line.name,
            'move_id': move_id.id,
            'product_id': line.product_id.id,
            'quantity': line.quantity,
            'credit': line.additional_landed_cost,
            'account_id': credit_account_id})

        #Create account move lines for quants already out of stock
        if qty_out > 0:
            AccountMoveLine.create({'name': line.name + ": " + str(qty_out) + _(' already out'),
                                    'move_id': move_id.id,
                                    'product_id': line.product_id.id,
                                    'quantity': qty_out,
                                    'credit': line.additional_landed_cost * qty_out / line.quantity,
                                    'account_id': debit_account_id})
            AccountMoveLine.create({'name': line.name + ": " + str(qty_out) + _(' already out'),
                                    'move_id': move_id.id,
                                    'product_id': line.product_id.id,
                                    'quantity': qty_out,
                                    'debit': line.additional_landed_cost * qty_out / line.quantity,
                                    'account_id': already_out_account_id})
        return True

    def _create_account_move(self):
        vals = {
            'journal_id': self.account_journal_id.id,
            'period_id': self.env['account.period'].find(self.date).id,
            'date': self.date,
            'ref': self.name
        }
        return self.env['account.move'].create(vals)

    def _check_sum(self, landed_cost):
        """
        Will check if each cost line its valuation lines sum to the correct amount
        and if the overall total amount is correct also
        """
        costcor = {}
        tot = 0
        for valuation_line in landed_cost.valuation_adjustment_lines:
            if costcor.get(valuation_line.cost_line_id):
                costcor[valuation_line.cost_line_id] += valuation_line.additional_landed_cost
            else:
                costcor[valuation_line.cost_line_id] = valuation_line.additional_landed_cost
            tot += valuation_line.additional_landed_cost
        res = (tot == landed_cost.amount_total)
        for costl in costcor.keys():
            if costcor[costl] != costl.price_unit:
                res = False
        return res

    @api.multi
    def button_validate(self):
        for cost in self:
            if not cost.valuation_adjustment_lines.ids or not self._check_sum(cost):
                raise UserError(_('You cannot validate a landed cost which has no valid valuation lines.'))
            move_id = self._create_account_move()
            for line in cost.valuation_adjustment_lines:
                if not line.move_id:
                    continue
                per_unit = line.final_cost / line.quantity
                diff = per_unit - line.former_cost_per_unit
                quants = [quant for quant in line.move_id.quant_ids]
                for quant in quants:
                    if quant.cost:
                        quant.cost = quant.cost + diff
                    else:
                        quant.cost += diff
                qty_out = 0
                for quant in line.move_id.quant_ids:
                    if quant.location_id.usage != 'internal':
                        qty_out += quant.qty
                cost._create_accounting_entries(line, move_id, qty_out)
            cost.write({'state': 'done', 'account_move_id': move_id.id})
        return True

    @api.model
    def button_cancel(self):
        self.write({'state': 'cancel'})
        return True

    @api.multi
    def compute_landed_cost(self):
        StockValuationLine = self.env['stock.valuation.adjustment.lines']
        unlink_ids = StockValuationLine.search([('cost_id', 'in', self.ids)])
        unlink_ids.unlink()
        for cost in self:
            if not cost.picking_ids:
                continue
            picking_ids = [p.id for p in cost.picking_ids]
            total_qty = 0.0
            total_cost = 0.0
            total_weight = 0.0
            total_volume = 0.0
            total_line = 0.0
            vals = cost.get_valuation_lines(picking_ids=picking_ids)
            for v in vals:
                for line in cost.cost_lines:
                    v.update({'cost_id': cost.id, 'cost_line_id': line.id})
                    StockValuationLine.create(v)
                total_qty += v.get('quantity', 0.0)
                total_cost += v.get('former_cost', 0.0)
                total_weight += v.get('weight', 0.0)
                total_volume += v.get('volume', 0.0)
                total_line += 1

            for line in cost.cost_lines:
                for valuation in cost.valuation_adjustment_lines:
                    value = 0.0
                    if valuation.cost_line_id and valuation.cost_line_id.id == line.id:
                        if line.split_method == 'by_quantity' and total_qty:
                            per_unit = (line.price_unit / total_qty)
                            value = valuation.quantity * per_unit
                        elif line.split_method == 'by_weight' and total_weight:
                            per_unit = (line.price_unit / total_weight)
                            value = valuation.weight * per_unit
                        elif line.split_method == 'by_volume' and total_volume:
                            per_unit = (line.price_unit / total_volume)
                            value = valuation.volume * per_unit
                        elif line.split_method == 'equal':
                            value = (line.price_unit / total_line)
                        elif line.split_method == 'by_current_cost_price' and total_cost:
                            per_unit = (line.price_unit / total_cost)
                            value = valuation.former_cost * per_unit
                        else:
                            value = (line.price_unit / total_line)
                    valuation.write({'additional_landed_cost': value})
        return True

    def _track_subtype(self, init_values):
        if 'state' in init_values and self.state == 'done':
            return 'stock_landed_costs.mt_stock_landed_cost_open'
        return super(StockLandedCost, self)._track_subtype(init_values)

class StockLandedCostLines(models.Model):
    _name = 'stock.landed.cost.lines'
    _description = 'Stock Landed Cost Lines'

    @api.multi
    def onchange_product_id(self, product_id=False):
        result = {}
        if not product_id:
            return {'value': {'quantity': 0.0, 'price_unit': 0.0}}

        product = self.env['product.product'].browse(product_id)
        result['name'] = product.name
        result['split_method'] = product.split_method
        result['price_unit'] = product.standard_price
        result['account_id'] = product.property_account_expense and product.property_account_expense.id or product.categ_id.property_account_expense_categ.id
        return {'value': result}

    name = fields.Char('Description')
    cost_id = fields.Many2one('stock.landed.cost', 'Landed Cost', required=True, ondelete='cascade')
    product_id = fields.Many2one('product.product', 'Product', required=True)
    price_unit = fields.Float('Cost', required=True, digits_compute=dp.get_precision('Product Price'))
    split_method = fields.Selection(product.SPLIT_METHOD, required=True)
    account_id = fields.Many2one('account.account', 'Account', domain=[('type', '<>', 'view'), ('type', '<>', 'closed')])

class StockValuationAdjustmentLines(models.Model):
    _name = 'stock.valuation.adjustment.lines'
    _description = 'Stock Valuation Adjustment Lines'

    @api.depends('former_cost', 'quantity', 'additional_landed_cost')
    def _amount_final(self):
        for line in self:
            line.former_cost_per_unit = (line.former_cost / line.quantity if line.quantity else 1.0)
            line.final_cost = (line.former_cost + line.additional_landed_cost)

    @api.depends('product_id', 'cost_line_id')
    def _get_name(self):
        for line in self:
            line.name = line.product_id.code or line.product_id.name or ''
            if line.cost_line_id:
                line.name += ' - ' + line.cost_line_id.name

    name = fields.Char(compute='_get_name', string='Description', store=True)
    cost_id = fields.Many2one('stock.landed.cost', 'Landed Cost', required=True, ondelete='cascade')
    cost_line_id = fields.Many2one('stock.landed.cost.lines', 'Cost Line', readonly=True)
    move_id = fields.Many2one('stock.move', 'Stock Move', readonly=True)
    product_id = fields.Many2one('product.product', 'Product', required=True)
    quantity = fields.Float(digits_compute=dp.get_precision('Product Unit of Measure'), default=1.0, required=True)
    weight = fields.Float(digits_compute=dp.get_precision('Product Unit of Measure'), default=1.0)
    volume = fields.Float(digits_compute=dp.get_precision('Product Unit of Measure'), default=1.0)
    former_cost = fields.Float(digits_compute=dp.get_precision('Product Price'))
    former_cost_per_unit = fields.Float(Compute='_amount_final', multi='cost', string='Former Cost(Per Unit)', digits_compute=dp.get_precision('Account'), store=True)
    additional_landed_cost = fields.Float(digits_compute=dp.get_precision('Product Price'))
    final_cost = fields.Float(compute='_amount_final', multi='cost', digits_compute=dp.get_precision('Account'), store=True)
