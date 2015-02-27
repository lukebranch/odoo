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
    'nb_contracts': {'name': 'Contracts', 'code': 'nb_contracts', 'dir': 'up', 'prior': 9, 'type': 'last', 'add_symbol': ''},
}


def compute_rate(stat_type, old, new):
    direction = stat_types[stat_type]['dir']

    try:
        value = round(100.0 * (new-old) / old, 2)
    except ZeroDivisionError:
        value = 0
    color = 'oBlack'
    if value and direction == 'up':
        color = (value > 0) and 'oGreen' or 'oRed'
    if value and direction != 'up':
        color = (value < 0) and 'oGreen' or 'oRed'
    return int(value), color


class AccountContractDashboard(http.Controller):

    filtered_product_template_ids = []

    def get_filter_product_template(self):
        return lambda x: str(x.product_id.product_tmpl_id.id) in self.filtered_product_template_ids

    @http.route('/account_contract_dashboard', auth='user', website=True)
    def account_contract_dashboard(self, **kw):

        all_stats = sorted([stat_types[x] for x in stat_types], key=lambda k: k['prior'])
        product_templates = request.env['product.template'].search([('deferred_revenue_category_id', '!=', None)])

        if kw.get('product_template_filter'):
            self.filtered_product_template_ids = request.httprequest.args.getlist('product_template_filter')

        start_date = datetime.strptime(kw.get('start_date'), '%Y-%m-%d') if kw.get('start_date') else default_start_date
        end_date = datetime.strptime(kw.get('end_date'), '%Y-%m-%d') if kw.get('end_date') else default_end_date

        return http.request.render('account_contract_dashboard.dashboard', {
            'all_stats': all_stats,
            'product_templates': product_templates,
            'filtered_product_template_ids': self.filtered_product_template_ids,
            'start_date': start_date.strftime('%Y-%m-%d'),
            'end_date': end_date.strftime('%Y-%m-%d'),
            'currency': '€',
        })

    @http.route('/account_contract_dashboard/detailed/<string:stat_type>', auth='user', website=True)
    def stats(self, stat_type, **kw):

        product_templates = request.env['product.template'].search([('deferred_revenue_category_id', '!=', None)])

        if kw.get('product_template_filter'):
            self.filtered_product_template_ids = request.httprequest.args.getlist('product_template_filter')

        start_date = datetime.strptime(kw.get('start_date'), '%Y-%m-%d') if kw.get('start_date') else default_start_date
        end_date = datetime.strptime(kw.get('end_date'), '%Y-%m-%d') if kw.get('end_date') else default_end_date
        end_date_1_month_ago = end_date - relativedelta(months=+1)
        end_date_3_months_ago = end_date - relativedelta(months=+3)
        end_date_12_months_ago = end_date - relativedelta(months=+12)

        report_name = stat_types[stat_type]['name']

        value_now = self.calculate_stat_diff(stat_type, end_date - relativedelta(months=+1), end_date)
        value_1_month_ago = self.calculate_stat_diff(stat_type, end_date_1_month_ago - relativedelta(months=+1), end_date_1_month_ago)
        value_3_months_ago = self.calculate_stat_diff(stat_type, end_date_3_months_ago - relativedelta(months=+1), end_date_3_months_ago)
        value_12_months_ago = self.calculate_stat_diff(stat_type, end_date_12_months_ago - relativedelta(months=+1), end_date_12_months_ago)

        stats_by_plan = [] if stat_type in ['nrr', 'arpu'] else sorted(self.get_stats_by_plan(stat_type, end_date), key=lambda k: k['value'], reverse=True)

        return http.request.render('account_contract_dashboard.detailed_dashboard', {
            'stat_type': stat_type,
            'product_templates': product_templates,
            'filtered_product_template_ids': self.filtered_product_template_ids,
            'currency': '€',
            'report_name': report_name,
            'start_date': start_date.strftime('%Y-%m-%d'),
            'end_date': end_date.strftime('%Y-%m-%d'),
            'value_now': value_now,
            'value_1_month_ago': value_1_month_ago,
            'value_3_months_ago': value_3_months_ago,
            'value_12_months_ago': value_12_months_ago,
            'currency': '€',
            'rate': compute_rate,
            'stats_by_plan': stats_by_plan,
        })

    def get_stats_by_plan(self, stat_type, date):

        results = []
        recurring_invoice_line_ids = request.env['account.invoice.line'].search([
            ('asset_start_date', '<=', date),
            ('asset_end_date', '>=', date),
            ('asset_category_id', '!=', None)
        ])

        plans = recurring_invoice_line_ids.mapped('product_id').mapped('product_tmpl_id')
        if self.filtered_product_template_ids:
            plans = plans.filtered(lambda x: str(x.id) in self.filtered_product_template_ids)

        for plan in plans:
            # TODO: filter according to plan
            invoice_line_ids_filter = lambda x: x.product_id.product_tmpl_id == plan
            filtered_invoice_line_ids = recurring_invoice_line_ids.filtered(invoice_line_ids_filter)
            results.append({
                'name': plan.name,
                'nb_customers': len(filtered_invoice_line_ids.mapped('account_analytic_id')),
                'value': self.calculate_stat_diff(stat_type, date - relativedelta(months=+1), date, invoice_line_ids_filter=invoice_line_ids_filter)['value'],
            })

        return results

    @http.route('/account_contract_dashboard/calculate_graph_stat', type="json", auth='user', website=True)
    def calculate_graph_stat(self, stat_type, start_date, end_date):

        # print('Calculate graph for %s between %s and %s' % (stat_type, start_date, end_date))

        start_date = datetime.strptime(start_date, '%Y-%m-%d')
        end_date = datetime.strptime(end_date, '%Y-%m-%d')

        delta = end_date - start_date

        results = []

        # Use request.env['account.invoice.line'].read_group([], '', groupby=['create_date:day']) instead
        for i in range(delta.days):
            date = start_date + timedelta(days=i)
            value = self.calculate_stat(stat_type, date)
            # results.append([str(date).split(' ')[0], value])
            results.append({
                '0': str(date).split(' ')[0],
                '1': value,
            })

        return results

    @http.route('/account_contract_dashboard/calculate_graph_mrr_growth', type="json", auth='user', website=True)
    def calculate_graph_mrr_growth(self, start_date, end_date):

        # THIS IS ROLLING MONTH CALCULATION

        start_date = datetime.strptime(start_date, '%Y-%m-%d')
        end_date = datetime.strptime(end_date, '%Y-%m-%d')

        delta = end_date - start_date

        results = [[], [], [], []]

        # Use request.env['account.invoice.line'].read_group([], '', groupby=['create_date:day']) instead
        for i in range(delta.days):
            date = start_date + timedelta(days=i)
            date_30_days_ago = date - relativedelta(months=+1)
            new_mrr = self.calculate_stat_aggregate('new_mrr', date_30_days_ago, date)
            expansion_mrr = 0  # self.calculate_stat_aggregate('expansion_mrr', date_30_days_ago, date)
            churned_mrr = 0  # self.calculate_stat_aggregate('churned_mrr', date_30_days_ago, date)
            net_new_mrr = new_mrr + expansion_mrr - churned_mrr

            print(net_new_mrr)

            results[0].append({
                '0': str(date).split(' ')[0],
                '1': new_mrr,
            })
            results[1].append({
                '0': str(date).split(' ')[0],
                '1': expansion_mrr,
            })
            results[2].append({
                '0': str(date).split(' ')[0],
                '1': churned_mrr,
            })
            results[3].append({
                '0': str(date).split(' ')[0],
                '1': net_new_mrr,
            })

        return results

    @http.route('/account_contract_dashboard/calculate_stats_diff', type="json", auth='user', website=True)
    def calculate_stats_diff(self, start_date, end_date):

        # Used in global dashboard

        results = {}

        for stat_type in stat_types:
            results[stat_type] = self.calculate_stat_diff(stat_type, start_date, end_date, add_symbol=True)

        return results

    def calculate_stat_diff(self, stat_type, start_date, end_date, invoice_line_ids_filter=None, add_symbol=False):

        if type(start_date) == datetime:
            start_date = start_date.strftime('%Y-%m-%d')
        if type(end_date) == datetime:
            end_date = end_date.strftime('%Y-%m-%d')

        start_date_30_days_ago = (datetime.strptime(start_date, '%Y-%m-%d') - relativedelta(months=+1)).strftime('%Y-%m-%d')
        end_date_30_days_ago = (datetime.strptime(end_date, '%Y-%m-%d') - relativedelta(months=+1)).strftime('%Y-%m-%d')

        if stat_types[stat_type]['type'] == 'last':
                value_30_days_ago = self.calculate_stat(stat_type, end_date_30_days_ago, invoice_line_ids_filter=invoice_line_ids_filter)
                value_end = self.calculate_stat(stat_type, end_date, invoice_line_ids_filter=invoice_line_ids_filter)
        elif stat_types[stat_type]['type'] == 'sum':
            # If sum, we aggregate all values between start_date and end_date
            value_30_days_ago = self.calculate_stat_aggregate(stat_type, start_date_30_days_ago, end_date_30_days_ago, invoice_line_ids_filter=invoice_line_ids_filter)
            value_end = self.calculate_stat_aggregate(stat_type, start_date, end_date, invoice_line_ids_filter=invoice_line_ids_filter)

        perc = 0 if value_30_days_ago == 0 else round(100*(value_end - value_30_days_ago)/float(value_30_days_ago), 1)

        if perc == 0:
            color = 'oBlack'
        elif stat_types[stat_type]['dir'] == 'up':
            color = 'oGreen' if perc > 0 else 'oRed'
        elif stat_types[stat_type]['dir'] == 'down':
            color = 'oRed' if perc > 0 else 'oGreen'

        result = {
            'value_30_days_ago': str(value_30_days_ago) + stat_types[stat_type]['add_symbol'] if add_symbol else value_30_days_ago,
            'value': str(value_end) + stat_types[stat_type]['add_symbol'] if add_symbol else value_end,
            'perc': perc,
            'color': color,
        }
        return result

    def calculate_stat_aggregate(self, stat_type, start_date, end_date, invoice_line_ids_filter=None):

        result = 0

        if type(start_date) == str:
            start_date = datetime.strptime(start_date, '%Y-%m-%d')
        if type(end_date) == str:
            end_date = datetime.strptime(end_date, '%Y-%m-%d')

        delta = end_date - start_date

        # Use request.env['account.invoice.line'].read_group([], '', groupby=['create_date:day']) instead
        for i in range(delta.days):
            date = start_date + timedelta(days=i)
            value = self.calculate_stat(stat_type, date, invoice_line_ids_filter=invoice_line_ids_filter)
            result += value

        return result

    # @profile
    def calculate_stat(self, stat_type, date, invoice_line_ids_filter=None):

        # print('calculate_stats_diff for %s' % (date))
        # if type(date) == datetime:
        #     date = date.strftime('%Y-%m-%d')

        if type(date) == str:
            date = datetime.strptime(date, '%Y-%m-%d')

        date_minus_1_days = (date - relativedelta(days=+1)).strftime(DEFAULT_SERVER_DATETIME_FORMAT)
        # date_minus_1_months = (date - relativedelta(months=+1)).strftime(DEFAULT_SERVER_DATETIME_FORMAT)
        date_plus_1_days = (date + relativedelta(days=+1)).strftime(DEFAULT_SERVER_DATETIME_FORMAT)

        # TODO: improve efficiency by calculate only once and give them in kw
        all_invoice_line_ids = request.env['account.invoice.line'].search([
            ('create_date', '<=', date_plus_1_days),
            ('create_date', '>=', date_minus_1_days),
        ])
        # grouped by account_id or account_analytic_id ?
        recurring_invoice_line_ids = request.env['account.invoice.line'].search([
            ('asset_start_date', '<=', date),
            ('asset_end_date', '>=', date),
            ('asset_category_id', '!=', None)
        ])
        non_recurring_invoice_line_ids = request.env['account.invoice.line'].search([
            ('create_date', '<=', date_plus_1_days),
            ('create_date', '>=', date_minus_1_days),
            ('asset_category_id', '=', None)
        ])

        if invoice_line_ids_filter:
            all_invoice_line_ids = all_invoice_line_ids.filtered(invoice_line_ids_filter)
            recurring_invoice_line_ids = recurring_invoice_line_ids.filtered(invoice_line_ids_filter)
            non_recurring_invoice_line_ids = non_recurring_invoice_line_ids.filtered(invoice_line_ids_filter)

        if self.filtered_product_template_ids:
            all_invoice_line_ids = all_invoice_line_ids.filtered(self.get_filter_product_template())
            recurring_invoice_line_ids = recurring_invoice_line_ids.filtered(self.get_filter_product_template())
            non_recurring_invoice_line_ids = non_recurring_invoice_line_ids.filtered(self.get_filter_product_template())

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

            # resigned_customers = [x for x in active_customers_1_month_ago if x not in active_customers_today]
            resigned_customers = active_customers_1_month_ago.filtered(lambda x: x not in active_customers_today)
            nb_avg_customers = (len(active_customers_1_month_ago) - len(active_customers_1_month_ago))/2.

            # print('%s resigned customers : %s' % (len(resigned_customers), resigned_customers))
            result = 0 if nb_avg_customers == 0 else len(resigned_customers)/float(nb_avg_customers)
            return result

        result = 0

        if stat_type == 'mrr':
            result = sum(recurring_invoice_line_ids.mapped('mrr'))
            result = int(result)

        elif stat_type == 'new_mrr':
            # import pudb; pudb.set_trace()
            new_recurring_invoice_line_ids = request.env['account.invoice.line'].search([
                ('asset_start_date', '=', date),
                ('asset_category_id', '!=', None)
            ])
            if new_recurring_invoice_line_ids:
                print('New invoice lines : %s for date %s' % (new_recurring_invoice_line_ids, date))
            result = sum(new_recurring_invoice_line_ids.mapped('mrr'))
            result = int(result)

        elif stat_type == 'churned_mrr':
            # TODO
            new_recurring_invoice_line_ids = request.env['account.invoice.line'].search([
                ('asset_start_date', '=', date),
                ('asset_category_id', '!=', None)
            ])
            result = sum(new_recurring_invoice_line_ids.mapped('mrr'))
            result = int(result)

        elif stat_type == 'expansion_mrr':
            # TODO
            new_recurring_invoice_line_ids = request.env['account.invoice.line'].search([
                ('asset_start_date', '=', date),
                ('asset_category_id', '!=', None)
            ])
            result = sum(new_recurring_invoice_line_ids.mapped('mrr'))
            result = int(result)

        elif stat_type == 'net_revenue':
            # TODO: use @MAT field instead of price_subtotal
            result = sum(all_invoice_line_ids.mapped('price_subtotal'))
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
            nb_contracts = len(recurring_invoice_line_ids.mapped('account_analytic_id'))
            avg_mrr_per_customer = 0 if not recurring_invoice_line_ids.mapped('account_analytic_id') else sum(recurring_invoice_line_ids.mapped('mrr')) / float(nb_contracts)
            logo_churn = _calculate_logo_churn()
            result = 0 if logo_churn == 0 else avg_mrr_per_customer/float(logo_churn)
            result = int(result)

        elif stat_type == 'logo_churn':
            result = 100*_calculate_logo_churn()
            result = round(result, 1)

        elif stat_type == 'revenue_churn':
            # TODO
            result = 0
            result = round(result, 1)

        elif stat_type == 'nb_contracts':
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
