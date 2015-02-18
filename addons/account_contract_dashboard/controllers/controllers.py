# -*- coding: utf-8 -*-
from openerp import http
from openerp.http import request
import datetime


class AccountContractDashboard(http.Controller):
    @http.route('/account_contract_dashboard', auth='user', website=True)
    def account_contract_dashboard(self, **kw):

        mrr = self.calculate_stat('mrr', datetime.date.today())
        default_date_from = datetime.date.today()
        default_date_to = datetime.date.today() + datetime.timedelta(days=30)
        return http.request.render('account_contract_dashboard.dashboard', {
            'mrr': mrr,
            'default_date_from': default_date_from,
            'default_date_to': default_date_to,
            'currency': '€',
        })

    @http.route('/account_contract_dashboard/detailed/<string:stat_type>', auth='user', website=True)
    def stats(self, stat_type, **kw):

        print('Render stat : %s' % stat_type)

        if stat_type == 'mrr':
            report_name = "Monthly Recurrent Revenue"

        default_date_from = datetime.date.today()
        default_date_to = datetime.date.today() + datetime.timedelta(days=30)

        return http.request.render('account_contract_dashboard.detailed_dashboard', {
            'stat_type': stat_type,
            'currency': '€',
            'report_name': report_name,
            'default_date_from': default_date_from,
            'default_date_to': default_date_to,
        })

    @http.route('/account_contract_dashboard/calculate', type="json", auth='user', website=True)
    def calculate_graph(self, stat_type, start_date, end_date):

        print('Calculate graph for %s between %s and %s' % (stat_type, start_date, end_date))

        start_date = datetime.datetime.strptime(start_date, '%Y-%m-%d')
        end_date = datetime.datetime.strptime(end_date, '%Y-%m-%d')

        delta = end_date - start_date

        results = []

        for i in range(delta.days):
            date = start_date + datetime.timedelta(days=i)
            value = self.calculate_stat(stat_type, date)
            results.append([str(date).split(' ')[0], value])

        return results

    def calculate_stat(self, stat_type, date):

        if stat_type == 'mrr':
            invoice_line_ids = request.env['account.invoice.line'].search([
                ('asset_category_id', '!=', None),
                ('asset_start_date', '<=', date),
                ('asset_end_date', '>=', date),
            ])
            # grouped by account_id or account_analytic_id ?

            mrr = sum(invoice_line_ids.mapped('mrr'))

            return mrr
        elif stat_type == 'churn':
            return 0
        else:
            return 0

        # churn = 0
        # logo_churn = 0
        # upgrade = 0
        # downgrade = 0
        # customer_life_time = 0  # 1/churn
        # customer_life_time_value = 0  # clt * mrr
