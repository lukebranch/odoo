# -*- coding: utf-8 -*-
from openerp import http
from openerp.http import request
from datetime import date


class AccountContractDashboard(http.Controller):
    @http.route('/account_contract_dashboard/', auth='public')
    def index(self, **kw):

        invoice_line_ids = request.env['account.invoice.line'].search([
            ('asset_category_id', '!=', None),
            ('asset_start_date', '<=', date.today()),
            ('asset_end_date', '>=', date.today()),
        ])
        print(invoice_line_ids)

        mrr = sum(invoice_line_ids.mapped('mrr'))
        # churn = 0
        # logo_churn = 0
        # upgrade = 0
        # downgrade = 0
        # customer_life_time = 0  # 1/churn
        # customer_life_time_value = 0  # clt * mrr
        return "MRR of today: %s" % mrr
