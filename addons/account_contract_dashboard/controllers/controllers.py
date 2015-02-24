# -*- coding: utf-8 -*-
from openerp import http
from openerp.http import request
from dateutil.relativedelta import relativedelta
from datetime import datetime, date, timedelta

from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT


default_start_date = date.today() - timedelta(days=30)
default_end_date = date.today()

stat_types = {
    'mrr': {'name': 'Monthly Recurrent Revenue', 'code': 'mrr', 'dir': 'up', 'prior': 1, 'type': 'last', 'add_symbol': '€'},
    'net_revenue': {'name': 'Net Revenue', 'code': 'net_revenue', 'dir': 'up', 'prior': 2, 'type': 'sum', 'add_symbol': '€'},
    'nrr': {'name': 'Non-Recurring Revenue', 'code': 'nrr', 'dir': 'up', 'prior': 3, 'type': 'sum', 'add_symbol': '€'},  # 'down' if fees ?
    'arpu': {'name': 'Average Revenue per Contract', 'code': 'arpu', 'dir': 'up', 'prior': 4, 'type': 'last', 'add_symbol': '€'},
    'arr': {'name': 'Annual Run-Rate', 'code': 'arr', 'dir': 'up', 'prior': 5, 'type': 'last', 'add_symbol': '€'},
    'ltv': {'name': 'Lifetime Value', 'code': 'ltv', 'dir': 'up', 'prior': 6, 'type': 'last', 'add_symbol': '€'},
    'logo_churn': {'name': 'Logo Churn', 'code': 'logo_churn', 'dir': 'down', 'prior': 7, 'type': 'last', 'add_symbol': '%'},
    'revenue_churn': {'name': 'Revenue Churn', 'code': 'revenue_churn', 'dir': 'down', 'prior': 8, 'type': 'last', 'add_symbol': '%'},
    'recurring_quant': {'name': 'Recurring Quantities', 'code': 'recurring_quant', 'dir': 'up', 'prior': 9, 'type': 'last', 'add_symbol': ''},
}


class AccountContractDashboard(http.Controller):
    @http.route('/account_contract_dashboard', auth='user', website=True)
    def account_contract_dashboard(self, **kw):

        all_stats = sorted([stat_types[x] for x in stat_types], key=lambda k: k['prior'])

        start_date = datetime.strptime(kw.get('start_date'), '%Y-%m-%d') if kw.get('start_date') else default_start_date
        end_date = datetime.strptime(kw.get('end_date'), '%Y-%m-%d') if kw.get('end_date') else default_end_date

        # print('Rendering dashboard between %s and %s' % (start_date, end_date))

        return http.request.render('account_contract_dashboard.dashboard', {
            'all_stats': all_stats,
            'start_date': start_date.strftime('%Y-%m-%d'),
            'end_date': end_date.strftime('%Y-%m-%d'),
            'currency': '€',
        })

    @http.route('/account_contract_dashboard/detailed/<string:stat_type>', auth='user', website=True)
    def stats(self, stat_type, **kw):

        start_date = datetime.strptime(kw.get('start_date'), '%Y-%m-%d') if kw.get('start_date') else default_start_date
        end_date = datetime.strptime(kw.get('end_date'), '%Y-%m-%d') if kw.get('end_date') else default_end_date

        # print('Render stat : %s' % stat_type)

        report_name = stat_types[stat_type]['name']

        value_now = self.calculate_stat(stat_type, end_date)
        value_1_month_ago = self.calculate_stat(stat_type, end_date - relativedelta(months=+1))
        value_3_month_ago = self.calculate_stat(stat_type, end_date - relativedelta(months=+3))
        value_12_month_ago = self.calculate_stat(stat_type, end_date - relativedelta(months=+12))

        # plans = A plan is defined by template lnked to the contract of a specific invoice line
        # --> grouped by invoice_line.product_id.product_tmpl_id.name

        return http.request.render('account_contract_dashboard.detailed_dashboard', {
            'stat_type': stat_type,
            'currency': '€',
            'report_name': report_name,
            'start_date': start_date.strftime('%Y-%m-%d'),
            'end_date': end_date.strftime('%Y-%m-%d'),
            'value_now': value_now,
            'value_1_month_ago': value_1_month_ago,
            'value_3_month_ago': value_3_month_ago,
            'value_12_month_ago': value_12_month_ago,
            'currency': '€',
        })

    @http.route('/account_contract_dashboard/calculate_graph', type="json", auth='user', website=True)
    def calculate_graph(self, stat_type, start_date, end_date):

        # print('Calculate graph for %s between %s and %s' % (stat_type, start_date, end_date))

        start_date = datetime.strptime(start_date, '%Y-%m-%d')
        end_date = datetime.strptime(end_date, '%Y-%m-%d')

        delta = end_date - start_date

        results = []

        for i in range(delta.days):
            date = start_date + timedelta(days=i)
            value = self.calculate_stat(stat_type, date)
            results.append([str(date).split(' ')[0], value])

        return results

    @http.route('/account_contract_dashboard/calculate_stats_diff', type="json", auth='user', website=True)
    def calculate_stats_diff(self, start_date, end_date):
        results = {}

        # time.sleep(2)

        # print('calculate_stats_diff between %s and %s' % (start_date, end_date))

        for stat_type in stat_types:
            value_start = self.calculate_stat(stat_type, start_date)
            value_end = self.calculate_stat(stat_type, end_date)
            perc = 0 if value_start == 0 else round(100*(value_end - value_start)/float(value_start), 1)
            if perc == 0:
                color = 'oBlack'
            elif stat_types[stat_type]['dir'] == 'up':
                color = 'oGreen' if perc > 0 else 'oRed'
            elif stat_types[stat_type]['dir'] == 'down':
                color = 'oRed' if perc > 0 else 'oGreen'

            results[stat_type] = {
                'value_start': str(value_start) + stat_types[stat_type]['add_symbol'],
                'value_end': str(value_end) + stat_types[stat_type]['add_symbol'],
                'perc': perc,
                'color': color,
            }

        print(results)

        return results

    def calculate_stat(self, stat_type, date):

        # print('calculate_stats_diff for %s' % (date))
        # if type(date) == datetime:
        #     date = date.strftime('%Y-%m-%d')

        if type(date) == str:
            date = datetime.strptime(date, '%Y-%m-%d')

        result = 0

        # TODO: improve efficiency by calculate only once and give them in kw
        # all_invoice_line_ids = request.env['account.invoice.line'].search([])

        # grouped by account_id or account_analytic_id ?
        recurring_invoice_line_ids = request.env['account.invoice.line'].search([
            ('asset_start_date', '<=', date),
            ('asset_end_date', '>=', date),
            ('asset_category_id', '!=', None)
        ])

        date_minus_1_days = (date - relativedelta(days=+1)).strftime(DEFAULT_SERVER_DATETIME_FORMAT)
        # date_minus_1_months = (date - relativedelta(months=+1)).strftime(DEFAULT_SERVER_DATETIME_FORMAT)
        date_plus_1_days = (date + relativedelta(days=+1)).strftime(DEFAULT_SERVER_DATETIME_FORMAT)

        # import pudb; pudb.set_trace()

        non_recurring_invoice_line_ids = request.env['account.invoice.line'].search([
            ('create_date', '<=', date_plus_1_days),
            ('create_date', '>=', date_minus_1_days),
            ('asset_category_id', '=', None)
        ])

        def _calculate_logo_churn():
            # [Baremetrics] (Cancelled Customers ÷ Previous Month's Active Customers) x 100
            # [Wiki] (Number of employees resigned during the month / Average number of employees during the month) x 100
            #   where Average number of employees during the month = (Total number of employees at the start of the month + Total number of employees at the end of the month) / 2.
            result = 0
            active_customers_today = recurring_invoice_line_ids.mapped('account_analytic_id')

            recurring_invoice_line_ids_1_month_ago = request.env['account.invoice.line'].search([
                ('asset_start_date', '<=', date - relativedelta(months=+1)),
                ('asset_end_date', '>=', date - relativedelta(months=+1)),
                ('asset_category_id', '!=', None)
            ])
            active_customers_1_month_ago = recurring_invoice_line_ids_1_month_ago.mapped('account_analytic_id')

            resigned_customers = [x for x in active_customers_1_month_ago if x not in active_customers_today]
            nb_avg_customers = (len(active_customers_1_month_ago) - len(active_customers_1_month_ago))/2.

            print('%s resigned customers : %s' % (len(resigned_customers), resigned_customers))
            result = 0 if nb_avg_customers == 0 else len(resigned_customers)/float(nb_avg_customers)
            return result

        if stat_type == 'mrr':
            result = sum(recurring_invoice_line_ids.mapped('mrr'))
            result = int(result)

        elif stat_type == 'net_revenue':
            # TODO: fix formula with aggregate
            result = sum(recurring_invoice_line_ids.mapped('mrr')) + sum(non_recurring_invoice_line_ids.mapped('price_subtotal'))
            result = int(result)

        elif stat_type == 'nrr':
            # TODO: use @MAT field instead of price_subtotal
            result = sum(non_recurring_invoice_line_ids.mapped('price_subtotal'))
            result = int(result)

        elif stat_type == 'arpu':
            mrr = sum(recurring_invoice_line_ids.mapped('mrr'))
            customers = recurring_invoice_line_ids.mapped('account_analytic_id')
            result = 0 if not customers else mrr/float(len(customers))
            result = int(result)

        elif stat_type == 'arr':
            result = sum(recurring_invoice_line_ids.mapped('mrr')) * 12
            result = int(result)

        elif stat_type == 'ltv':
            # LTV = Average Monthly Recurring Revenue Per Customer ÷ User Churn Rate
            avg_mrr_per_customer = 0 if not recurring_invoice_line_ids.mapped('account_analytic_id') else sum(recurring_invoice_line_ids.mapped('mrr')) / float(len(recurring_invoice_line_ids.mapped('account_analytic_id')))
            logo_churn = _calculate_logo_churn()
            result = 0 if logo_churn == 0 else avg_mrr_per_customer/float(logo_churn)
            result = int(result)

        elif stat_type == 'logo_churn':
            result = 100*_calculate_logo_churn()
            result = round(result, 1)

        elif stat_type == 'revenue_churn':
            result = 0
            result = round(result, 1)

        elif stat_type == 'recurring_quant':
            result = len(recurring_invoice_line_ids.mapped('account_analytic_id'))
        else:
            result = 0

        return result

        # churn = 0
        # logo_churn = 0
        # upgrade = 0
        # downgrade = 0
        # customer_life_time = 0  # 1/churn
        # customer_life_time_value = 0  # clt * mrr
