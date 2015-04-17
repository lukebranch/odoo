# -*- coding: utf-8 -*-

from openerp.tests import common

class TestProductExtendedCommon(common.TransactionCase):

    def setUp(self):
        super(TestProductExtendedCommon, self).setUp()

        self.MrpBom = self.env['mrp.bom']
        self.Product = self.env['product.product']
        categ_id = self.env.ref("product.product_category_5").id

        self.PCAssemble = self.Product.create({
            'name': 'PC Assemble and Customize',
            'standard_price': 600,
            'categ_id': categ_id,
            'type': 'consu',
            })

        self.IPadMini = self.Product.create({
            'name': 'PC Assemble and Customize',
            'standard_price': 800,
            'categ_id': categ_id,
            'type': 'consu',
            })

        self.RAMSR = self.Product.create({
            'name': 'PC Assemble and Customize',
            'standard_price': 78,
            'categ_id': categ_id,
            'type': 'consu',
            })

        self.IPod = self.Product.create({
            'name': 'PC Assemble and Customize',
            'standard_price': 14,
            'categ_id': categ_id,
            'type': 'consu',
            })

        self.HDDSH2 = self.Product.create({
            'name': 'HDD SH2 ',
            'standard_price': 1020,
            'categ_id': categ_id,
            'type': 'consu',
            })

        self.HDDSH1 = self.Product.create({
            'name': 'HDD SH1',
            'standard_price': 860,
            'categ_id': categ_id,
            'type': 'consu',
            })

