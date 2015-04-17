# -*- coding: utf-8 -*-

from openerp.addons.product_extended.tests.common import TestProductExtendedCommon

class TestComputePrice(TestProductExtendedCommon):

    def test_compute_standard_price(self):

        self.BillMaterial1 = self.MrpBom.create({
            'name': 'BillMaterial1',
            'product_tmpl_id': self.HDDSH2.product_tmpl_id.id,
            'product_qty': 1,
            'product_efficiency': 1,
            'bom_line_ids' : [(0, 0 , {
                'product_id': self.HDDSH1.id,
                'type': 'normal',
                'product_qty': 2,
                }),]
            })

        self.BillMaterial2 = self.MrpBom.create({
            'name': 'BillMaterial2',
            'product_tmpl_id': self.PCAssemble.product_tmpl_id.id,
            'product_qty': 1,
            'product_efficiency': 1,
            'bom_line_ids' : [(0, 0 , {
                'product_id': self.IPadMini.id,
                'type': 'normal',
                'product_qty': 1,
                }),
                (0, 0 , {
                'product_id': self.HDDSH2.id,
                'type': 'normal',
                'product_qty': 1,
                }),
                (0, 0 , {
                'product_id': self.RAMSR.id,
                'type': 'normal',
                'product_qty': 1,
                }),
                (0, 0 , {
                'product_id': self.IPod.id,
                'type': 'normal',
                'product_qty': 1,
                })]
            })


        context = {'no_update': False}
        # Calculate standard price without recursive
        totalprice1 = self.IPadMini.standard_price + self.HDDSH2.standard_price + self.RAMSR.standard_price + self.IPod.standard_price
        computeprice1 = self.BillMaterial2.product_tmpl_id.with_context(context).compute_standard_price(recursive=False, real_time_accounting=False)
        price1 = computeprice1[self.BillMaterial2.product_tmpl_id.id]

        self.assertEqual(
            totalprice1, price1, 'Wrong standard price calculate (Price must be %s instead of %s)' % (totalprice1, price1))

        # Calculate standard price with recursive
        totalprice2 = totalprice1 + (self.HDDSH1.standard_price * 2) - self.HDDSH2.standard_price
        computeprice2 = self.BillMaterial2.product_tmpl_id.with_context(context).compute_standard_price(recursive=True, real_time_accounting=False)
        price2 = computeprice2[self.BillMaterial2.product_tmpl_id.id]

        self.assertEqual(
            totalprice2, price2, 'Wrong standard price calculate (Price must be %s instead of %s)' % (totalprice2, price2))

