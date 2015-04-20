# -*- coding: utf-8 -*-
from datetime import datetime
from openerp.tests.common import TransactionCase


class TestStockInvoiceDirectly(TransactionCase):

    def setUp(self):
        super(TestStockInvoiceDirectly, self).setUp()

    def test_stock_invocie_directly(self):
        Picking = self.env['stock.picking']
        StockInvoiceOnshiping = self.env['stock.invoice.onshipping']
        AccountInvocie = self.env['account.invoice']

        move_lines = [
            (0, 0,
                {
                    'name': self.env.ref('product.product_product_3').name,
                    'location_id': self.env.ref('stock.stock_location_stock').id,
                    'product_id': self.env.ref('product.product_product_3').id,
                    'product_uom_qty': 3.0,
                    'product_uom': self.env.ref('product.product_uom_unit').id,
                    'location_dest_id': self.env.ref('stock.stock_location_customers').id,
                }
             )
        ]
        #I will create an outgoing picking order which creates an invoice from the picking order itself
        picking_ids = Picking.create(dict(
            partner_id=self.env.ref('base.res_partner_address_22').id,
            move_lines=move_lines,
            invoice_state='2binvoiced',
            move_type='direct',
            picking_type_id=self.env.ref('stock.picking_type_out').id,
            company_id=self.env.ref('base.main_company').id,
            priority='1',
        ))

        context = {"lang": "en_US", "search_default_available": 1,
                   "tz": False, "active_model": "ir.ui.menu", "contact_display": "partner", }

        #I need to check the availability of the product so I make my picking order for processing later.I need to check the availability of the product so I make my picking order for processing later.
        picking_ids.with_context(context).action_confirm()

        #I check the product availability. Product is available in the stock and ready to be sent.
        picking_ids.with_context(context).action_assign()

        #I process the delivery
        picking_ids.do_transfer()

        #As the Invoice state of the picking order is To be invoiced. I create invoice for my outgoing picking order.
        invoiceonship = StockInvoiceOnshiping.with_context(active_ids=picking_ids.ids).create(dict(
            invoice_date=datetime.now(),
            journal_id=self.env.ref('account.sales_journal').id,
        ))

        context = {"lang": "en_US",
                   "search_default_available": 1,
                   "tz": False,
                   "active_model": "stock.picking",
                   "contact_display": "partner",
                   "active_ids": picking_ids.ids,
                   "active_id": picking_ids.id, }

        invoiceonship.with_context(context).create_invoice()

        #I check that the customer invoice is created successfully.
        partner = picking_ids.partner_id.id
        self.assertTrue(AccountInvocie.search([('type', '=', 'out_invoice'), ('partner_id', '=', partner)]),
                        'No Invoice is generated!')
