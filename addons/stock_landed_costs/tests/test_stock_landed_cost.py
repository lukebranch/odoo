# -*- coding: utf-8 -*-
from openerp.tests.common import TransactionCase

class TestStockLandedCosts(TransactionCase):

    def setUp(self):
        super(TestStockLandedCosts, self).setUp()

    def test_stock_landed_costs(self):
        # In order to test the landed costs feature of stock, I create a landed cost, confirm it and check its account move created
        # I create 2 products with different volume and gross weight and configure them for real_time valuation and real price costing method
        Product = self.env['product.product']
        Picking = self.env['stock.picking']
        StockLandedCost = self.env['stock.landed.cost']

        product_1 = Product.create(dict(
            name="LC product 1",
            cost_method='real',
            valuation='real_time',
            weight=10,
            volume=1,
            property_stock_account_input=self.env.ref('account.o_expense').id,
            property_stock_account_output=self.env.ref('account.o_income').id
        ))
        product_2 = Product.create(dict(
            name="LC product 2",
            cost_method='real',
            valuation='real_time',
            weight=20,
            volume=1.5,
            property_stock_account_input=self.env.ref('account.o_expense').id,
            property_stock_account_output=self.env.ref('account.o_income').id
        ))

        #I create 2 picking moving those products
        move_line1 = [
            (0, 0,
                {
                    'name': 'move 1',
                    'product_id': product_1.id,
                    'product_uom_qty': 5,
                    'product_uom': self.env.ref('product.product_uom_unit').id,
                    'product_uos_qty': 5,
                    'product_uos': self.env.ref('product.product_uom_unit').id,
                    'location_id': self.env.ref('stock.stock_location_stock').id,
                    'location_dest_id': self.env.ref('stock.stock_location_customers').id,
                })
        ]
        picking_1 = Picking.create(dict(
            picking_type_id=self.env.ref('stock.picking_type_out').id,
            move_lines=move_line1,
        ))
        move_line2 = [
            (0, 0,
                {
                    'name': 'move 2',
                    'product_id': product_2.id,
                    'product_uom_qty': 5,
                    'product_uom': self.env.ref('product.product_uom_unit').id,
                    'product_uos_qty': 5,
                    'product_uos': self.env.ref('product.product_uom_unit').id,
                    'location_id': self.env.ref('stock.stock_location_stock').id,
                    'location_dest_id': self.env.ref('stock.stock_location_customers').id,
                })
        ]
        picking_2 = Picking.create(dict(
            picking_type_id=self.env.ref('stock.picking_type_out').id,
            move_lines=move_line2,
        ))

        #I create a landed cost for those 2 pickings
        cost_lines = [
            (0, 0,
                {
                    'name': 'equal split',
                    'split_method': 'equal',
                    'price_unit': 10,
                    'product_id': product_2.id, },
                {
                    'name': 'split by quantity',
                    'split_method': 'by_quantity',
                    'price_unit': 150,
                    'product_id': product_2.id, },
                {
                    'name': 'split by weight',
                    'split_method': 'by_weight',
                    'price_unit': 250,
                    'product_id': product_2.id, },
                {
                    'name': 'split by volume',
                    'split_method': 'by_volume',
                    'price_unit': 20,
                    'product_id': product_2.id, },
             )
        ]

        stock_landed_cost = StockLandedCost.create(dict(
            picking_ids=[(6, 0, [picking_1.id, picking_2.id])],
            account_journal_id=self.env.ref('account.expenses_journal').id,
            cost_lines=cost_lines,
            valuation_adjustment_lines=[]
        ))
        #I compute the landed cost  using Compute button
        stock_landed_cost.compute_landed_cost()

        #I check the valuation adjustment lines
        for valuation in stock_landed_cost.valuation_adjustment_lines:
            if valuation.cost_line_id.name == 'equal split':
                self.assertEqual(valuation.additional_landed_cost, 5)
            elif valuation.cost_line_id.name == 'split by quantity' and valuation.move_id.name == "move 1":
                self.assertEqual(valuation.additional_landed_cost, 50)
            elif valuation.cost_line_id.name == 'split by quantity' and valuation.move_id.name == "move 2":
                self.assertEqual(valuation.additional_landed_cost, 100)
            elif valuation.cost_line_id.name == 'split by weight' and valuation.move_id.name == "move 1":
                self.assertEqual(valuation.additional_landed_cost, 50)
            elif valuation.cost_line_id.name == 'split by weight' and valuation.move_id.name == "move 2":
                self.assertEqual(valuation.additional_landed_cost, 200)
            elif valuation.cost_line_id.name == 'split by volume' and valuation.move_id.name == "move 1":
                self.assertEqual(valuation.additional_landed_cost, 5)
            elif valuation.cost_line_id.name == 'split by volume' and valuation.move_id.name == "move 2":
                self.assertEqual(valuation.additional_landed_cost, 15)
            else:
                raise 'unrecognized valuation adjustment line'
        #I confirm the landed cost
        stock_landed_cost.button_validate()
        #I check that the landed cost is now "Closed" and that it has an accounting entry
        self.assertEqual(stock_landed_cost.state, 'done')
        self.assertTrue(stock_landed_cost.account_move_id)
        self.assertEqual(len(stock_landed_cost.account_move_id.line_id), 4)
