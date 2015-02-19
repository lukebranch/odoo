# -*- coding: utf-8 -*-
from openerp import http
from openerp.http import request
import datetime
import time
from dateutil.relativedelta import relativedelta


default_start_date = datetime.date.today() - datetime.timedelta(days=30)
default_end_date = datetime.date.today()

stat_types = {
    'mrr': {'name': 'Monthly Recurrent Revenue', 'code': 'mrr', 'dir': 'up', 'prior': 1},
    'net_revenue': {'name': 'Net Revenue', 'code': 'net_revenue', 'dir': 'up', 'prior': 2},
    'nrr': {'name': 'Non-Recurring Revenue', 'code': 'nrr', 'dir': 'up', 'prior': 3},  # 'down' if fees ?
    'avg_revenue': {'name': 'Average Revenue per Contract', 'code': 'avg_revenue', 'dir': 'up', 'prior': 4},
    'annual_rr': {'name': 'Annual Run-Rate', 'code': 'annual_rr', 'dir': 'up', 'prior': 5},
    'ltv': {'name': 'Lifetime Value', 'code': 'ltv', 'dir': 'up', 'prior': 6},
    'logo_churn': {'name': 'Logo Churn', 'code': 'logo_churn', 'dir': 'down', 'prior': 7},
    'revenue_churn': {'name': 'Revenue Churn', 'code': 'revenue_churn', 'dir': 'down', 'prior': 8},
    'recurring_quant': {'name': 'Recurring Quantities', 'code': 'recurring_quant', 'dir': 'up', 'prior': 9},
}


class AccountContractDashboard(http.Controller):
    @http.route('/account_contract_dashboard', auth='user', website=True)
    def account_contract_dashboard(self, **kw):

        all_stats = [stat_types[x] for x in stat_types]
        all_stats = sorted(all_stats, key=lambda k: k['prior'])

        return http.request.render('account_contract_dashboard.dashboard', {
            'all_stats': all_stats,
            'start_date': default_start_date,
            'end_date': default_end_date,
            'currency': '€',
        })

    @http.route('/account_contract_dashboard/detailed/<string:stat_type>', auth='user', website=True)
    def stats(self, stat_type, **kw):

        # start_date = kw.get('start_date') if kw.get('start_date') else default_start_date
        end_date = kw.get('end_date') if kw.get('end_date') else default_end_date

        print('Render stat : %s' % stat_type)

        report_name = stat_types[stat_type]['name']

        value_now = self.calculate_stat(stat_type, end_date)
        value_1_month_ago = self.calculate_stat(stat_type, end_date - relativedelta(months=+1))
        value_3_month_ago = self.calculate_stat(stat_type, end_date - relativedelta(months=+3))
        value_12_month_ago = self.calculate_stat(stat_type, end_date - relativedelta(months=+12))

        return http.request.render('account_contract_dashboard.detailed_dashboard', {
            'stat_type': stat_type,
            'currency': '€',
            'report_name': report_name,
            'start_date': default_start_date,
            'end_date': default_end_date,
            'value_now': value_now,
            'value_1_month_ago': value_1_month_ago,
            'value_3_month_ago': value_3_month_ago,
            'value_12_month_ago': value_12_month_ago,
            'currency': '€',
        })

    @http.route('/account_contract_dashboard/calculate_graph', type="json", auth='user', website=True)
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

    @http.route('/account_contract_dashboard/calculate_stats_diff', type="json", auth='user', website=True)
    def calculate_stats_diff(self, start_date, end_date):
        results = {}

        time.sleep(2)

        for stat_type in stat_types:
            value_start = self.calculate_stat(stat_type, start_date)
            value_end = self.calculate_stat(stat_type, end_date)
            perc = 0 if value_start == 0 else (value_end - value_start)/float(value_start)
            color = 'oGreen' if perc > 0 else 'oRed'
            results[stat_type] = {
                'value_start': str(value_start) + '€',
                'value_end': str(value_end) + '€',
                'perc': perc,
                'color': color,
            }

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

        elif stat_type == 'net_revenue':
            return 0

        elif stat_type == 'nrr':
            return 0

        elif stat_type == 'avg_revenue':
            return 0

        elif stat_type == 'annual_rr':
            return 0

        elif stat_type == 'ltv':
            return 0

        elif stat_type == 'logo_churn':
            return 0

        elif stat_type == 'revenue_churn':
            return 0

        elif stat_type == 'recurring_quant':
            return 0

        else:
            return 0

        # churn = 0
        # logo_churn = 0
        # upgrade = 0
        # downgrade = 0
        # customer_life_time = 0  # 1/churn
        # customer_life_time_value = 0  # clt * mrr
