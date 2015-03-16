# -*- coding: utf-8 -*-
from openerp import http
from openerp.http import request
from dateutil.relativedelta import relativedelta
from datetime import datetime, date, timedelta
from math import floor

from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT, DEFAULT_SERVER_DATE_FORMAT


default_start_date = date.today() - timedelta(days=30)
default_end_date = date.today()

stat_types = {
    'mrr': {'name': 'Monthly Recurring Revenue', 'code': 'mrr', 'dir': 'up', 'prior': 1, 'type': 'last', 'add_symbol': '€'},
    'net_revenue': {'name': 'Net Revenue', 'code': 'net_revenue', 'dir': 'up', 'prior': 2, 'type': 'sum', 'add_symbol': '€'},
    'nrr': {'name': 'Non-Recurring Revenue', 'code': 'nrr', 'dir': 'up', 'prior': 3, 'type': 'sum', 'add_symbol': '€'},  # 'down' if fees ?
    'arpu': {'name': 'Average Revenue per Contract', 'code': 'arpu', 'dir': 'up', 'prior': 4, 'type': 'last', 'add_symbol': '€'},
    'arr': {'name': 'Annual Run-Rate', 'code': 'arr', 'dir': 'up', 'prior': 5, 'type': 'last', 'add_symbol': '€'},
    'ltv': {'name': 'Lifetime Value', 'code': 'ltv', 'dir': 'up', 'prior': 6, 'type': 'last', 'add_symbol': '€'},
    'logo_churn': {'name': 'Logo Churn', 'code': 'logo_churn', 'dir': 'down', 'prior': 7, 'type': 'last', 'add_symbol': '%'},
    'revenue_churn': {'name': 'Revenue Churn', 'code': 'revenue_churn', 'dir': 'down', 'prior': 8, 'type': 'last', 'add_symbol': '%'},
    'nb_contracts': {'name': 'Contracts', 'code': 'nb_contracts', 'dir': 'up', 'prior': 9, 'type': 'last', 'add_symbol': ''},
}

forecast_types = {
    'mrr': {'name': 'Forecasted Annual MRR Growth', 'code': 'forecast_mrr', 'prior': 1},
    'contracts': {'name': 'Forecasted Annual Contracts Growth', 'code': 'forecast_contracts', 'prior': 2},
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

    def get_filter_contract_template(self, filtered_contract_template_ids):
        return lambda x: str(x.account_analytic_id.template_id.id) in filtered_contract_template_ids

    def get_filter_out_invoice(self):
        return lambda x: x.invoice_id.type == 'out_invoice'

    @http.route('/account_contract_dashboard', auth='user', website=True)
    def account_contract_dashboard(self, **kw):

        all_stats = sorted([stat_types[x] for x in stat_types], key=lambda k: k['prior'])
        all_forecasts = sorted([forecast_types[x] for x in forecast_types], key=lambda k: k['prior'])

        contract_templates = request.env['account.analytic.account'].search([('type', '=', 'template')])

        filtered_contract_template_ids = request.httprequest.args.getlist('contract_template_filter') if kw.get('contract_template_filter') else []

        start_date = datetime.strptime(kw.get('start_date'), '%Y-%m-%d') if kw.get('start_date') else default_start_date
        end_date = datetime.strptime(kw.get('end_date'), '%Y-%m-%d') if kw.get('end_date') else default_end_date

        href_post_args = 'start_date=%s&end_date=%s&' % (start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d'))
        for item in filtered_contract_template_ids:
            href_post_args += 'contract_template_filter=%s&' % item

        return http.request.render('account_contract_dashboard.dashboard', {
            'all_stats': all_stats,
            'all_forecast': all_forecasts,
            'contract_templates': contract_templates,
            'filtered_contract_template_ids': filtered_contract_template_ids,
            'start_date': start_date.strftime('%Y-%m-%d'),
            'end_date': end_date.strftime('%Y-%m-%d'),
            'href_post_args': href_post_args,
        })

    @http.route('/account_contract_dashboard/detailed/<string:stat_type>', auth='user', website=True)
    def stats(self, stat_type, **kw):

        contract_templates = request.env['account.analytic.account'].search([('type', '=', 'template')])

        filtered_contract_template_ids = request.httprequest.args.getlist('contract_template_filter') if kw.get('contract_template_filter') else []

        start_date = datetime.strptime(kw.get('start_date'), '%Y-%m-%d') if kw.get('start_date') else default_start_date
        end_date = datetime.strptime(kw.get('end_date'), '%Y-%m-%d') if kw.get('end_date') else default_end_date

        report_name = stat_types[stat_type]['name']

        value_now = self.calculate_stat_diff(stat_type, start_date - relativedelta(months=+1),  end_date - relativedelta(months=+1), start_date, end_date, filtered_contract_template_ids=filtered_contract_template_ids)
        value_1_month_ago = self.calculate_stat_diff(stat_type, start_date - relativedelta(months=+2), end_date - relativedelta(months=+2), start_date - relativedelta(months=+1), end_date - relativedelta(months=+1), filtered_contract_template_ids=filtered_contract_template_ids)
        value_3_months_ago = self.calculate_stat_diff(stat_type, start_date - relativedelta(months=+4), end_date - relativedelta(months=+4), start_date - relativedelta(months=+3), end_date - relativedelta(months=+3), filtered_contract_template_ids=filtered_contract_template_ids)
        value_12_months_ago = self.calculate_stat_diff(stat_type, start_date - relativedelta(months=+13), end_date - relativedelta(months=+13), start_date - relativedelta(months=+12), end_date - relativedelta(months=+12), filtered_contract_template_ids=filtered_contract_template_ids)

        href_post_args = 'start_date=%s&end_date=%s&' % (start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d'))
        for item in filtered_contract_template_ids:
            href_post_args += 'contract_template_filter=%s&' % item

        return http.request.render('account_contract_dashboard.detailed_dashboard', {
            'all_stats': stat_types,
            'stat_type': stat_type,
            'contract_templates': contract_templates,
            'filtered_contract_template_ids': filtered_contract_template_ids,
            'currency': '€',
            'report_name': report_name,
            'start_date': start_date.strftime('%Y-%m-%d'),
            'end_date': end_date.strftime('%Y-%m-%d'),
            'value_now': value_now,
            'value_1_month_ago': value_1_month_ago,
            'value_3_months_ago': value_3_months_ago,
            'value_12_months_ago': value_12_months_ago,
            'display_stats_by_plan': False if stat_type in ['nrr', 'arpu', 'logo_churn'] else True,
            'currency': '€',
            'rate': compute_rate,
            'href_post_args': href_post_args,
        })

    @http.route('/account_contract_dashboard/forecast', auth='user', website=True)
    def forecast(self, **kw):

        currency = request.env['res.company'].search([])[0].currency_id.symbol

        return http.request.render('account_contract_dashboard.forecast', {
            'currency': currency,
        })

    @http.route('/account_contract_dashboard/get_default_values_forecast', type="json", auth='user', website=True)
    def get_default_values_forecast(self, forecast_type=None):

        mrr = self.calculate_stat('mrr', date.today())
        net_new_mrr = self.calculate_stat('net_new_mrr', date.today())[3]
        revenue_churn = self.calculate_stat('revenue_churn', date.today())
        nb_contracts = self.calculate_stat('nb_contracts', date.today())
        arpu = self.calculate_stat('arpu', date.today())

        currency = request.env['res.company'].search([])[0].currency_id.symbol

        if forecast_type:
            if forecast_type == 'forecast_mrr':
                return {
                    'currency': currency,
                    'starting_value': mrr,
                    'growth_linear': net_new_mrr,
                    'growth_expon': 15,
                    'churn': revenue_churn,
                    'projection_time': 12,
                }
            else:
                return {
                    'currency': '',
                    'starting_value': nb_contracts,
                    'growth_linear': 0 if arpu == 0 else int(net_new_mrr/arpu),
                    'growth_expon': 15,
                    'churn': revenue_churn,
                    'projection_time': 12,
                }

        # If return both
        return {
            'currency': currency,
            'starting_mrr': mrr,
            'revenue_growth_linear': net_new_mrr,
            'revenue_growth_expon': 15,
            'revenue_churn': revenue_churn,
            'starting_contracts': nb_contracts,
            'contracts_growth_linear': 0 if arpu == 0 else int(net_new_mrr/arpu),
            'contracts_growth_expon': 15,
            'contracts_churn': revenue_churn,
            'projection_time': 12,
        }

    @http.route('/account_contract_dashboard/get_stats_by_plan', type="json", auth='user', website=True)
    def get_stats_by_plan(self, stat_type, date, filtered_contract_template_ids=None):

        results = []
        recurring_invoice_line_ids = request.env['account.invoice.line'].search([
            ('asset_start_date', '<=', date),
            ('asset_end_date', '>=', date),
            ('asset_category_id', '!=', None),
            ('mrr', '>', 0),
        ])

        plans = request.env['account.analytic.account'].search([('type', '=', 'template')])

        if filtered_contract_template_ids:
            plans = plans.filtered(lambda x: str(x.id) in filtered_contract_template_ids)

        for plan in plans:
            invoice_line_ids_filter = lambda x: x.account_analytic_id.template_id.id == plan.id
            filtered_invoice_line_ids = recurring_invoice_line_ids.filtered(invoice_line_ids_filter)
            results.append({
                'name': plan.name,
                'nb_customers': len(filtered_invoice_line_ids.mapped('account_analytic_id')),
                'value': self.calculate_stat(stat_type, date, invoice_line_ids_filter=invoice_line_ids_filter, filtered_contract_template_ids=filtered_contract_template_ids),
            })

        results = sorted((results), key=lambda k: k['value'], reverse=True)

        return results, stat_types

    @http.route('/account_contract_dashboard/calculate_graph_stat', type="json", auth='user', website=True)
    def calculate_graph_stat(self, stat_type, start_date, end_date, filtered_contract_template_ids, complete=False, nb_points=30):

        def get_pruned_tick_values(ticks, start_date, end_date, nb_desired_ticks):
            nb_values = len(ticks)
            keep_one_of = max(1, floor(nb_values / float(nb_desired_ticks)))

            ticks = [x for x in ticks if x % keep_one_of == 0]

            return ticks

        start_date = datetime.strptime(start_date, '%Y-%m-%d')
        end_date = datetime.strptime(end_date, '%Y-%m-%d')

        delta = end_date - start_date
        ticks = range(delta.days + 1)

        if not complete:
            ticks = get_pruned_tick_values(ticks, start_date, end_date, nb_points)

        results = []

        for i in ticks:

            # METHOD NON-OPTIMIZED

            date = start_date + timedelta(days=i)
            value = self.calculate_stat(stat_type, date, filtered_contract_template_ids=filtered_contract_template_ids)
            results.append({
                '0': str(date).split(' ')[0],
                '1': value,
            })

            # METHOD OPTIMIZED : pass search in argument only if usefull
            # TODO

        return stat_types[stat_type]['name'], results

    @http.route('/account_contract_dashboard/calculate_graph_mrr_growth', type="json", auth='user', website=True)
    def calculate_graph_mrr_growth(self, start_date, end_date, filtered_contract_template_ids):

        # THIS IS ROLLING MONTH CALCULATION

        start_date = datetime.strptime(start_date, '%Y-%m-%d')
        end_date = datetime.strptime(end_date, '%Y-%m-%d')

        delta = end_date - start_date

        results = [[], [], [], []]

        # Use request.env['account.invoice.line'].read_group([], '', groupby=['create_date:day']) instead
        for i in range(delta.days + 1):
            date = start_date + timedelta(days=i)

            new_mrr, expansion_mrr, churned_mrr, net_new_mrr = self.calculate_stat('net_new_mrr', date, filtered_contract_template_ids=filtered_contract_template_ids)
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

    @http.route('/account_contract_dashboard/calculate_stats_diff_30_days_ago', type="json", auth='user', website=True)
    def calculate_stats_diff(self, stat_type, start_date, end_date, filtered_contract_template_ids):

        results = {}

        # Used in global dashboard
        if type(start_date) == str:
            # print('CAREFULL, DATE IN STR')
            start_date = datetime.strptime(start_date, '%Y-%m-%d')
        if type(end_date) == str:
            # print('CAREFULL, DATE IN STR')
            end_date = datetime.strptime(end_date, '%Y-%m-%d')
        start_date_1 = start_date - relativedelta(months=+1)
        end_date_1 = end_date - relativedelta(months=+1)
        start_date_2 = start_date
        end_date_2 = end_date

        results = self.calculate_stat_diff(stat_type, start_date_1, end_date_1, start_date_2, end_date_2, add_symbol=True, filtered_contract_template_ids=filtered_contract_template_ids)

        return results

    def calculate_stat_diff(self, stat_type, start_date_1, end_date_1, start_date_2, end_date_2, invoice_line_ids_filter=None, add_symbol=False, filtered_contract_template_ids=None):

        if stat_types[stat_type]['type'] == 'last':
            value_1 = self.calculate_stat(stat_type, end_date_1, filtered_contract_template_ids=filtered_contract_template_ids, invoice_line_ids_filter=invoice_line_ids_filter)
            value_2 = self.calculate_stat(stat_type, end_date_2, filtered_contract_template_ids=filtered_contract_template_ids, invoice_line_ids_filter=invoice_line_ids_filter)
        elif stat_types[stat_type]['type'] == 'sum':
            # If sum, we aggregate all values between start_date and end_date
            value_1 = self.calculate_stat_aggregate(stat_type, start_date_1, end_date_1, filtered_contract_template_ids=filtered_contract_template_ids, invoice_line_ids_filter=invoice_line_ids_filter)
            value_2 = self.calculate_stat_aggregate(stat_type, start_date_2, end_date_2, filtered_contract_template_ids=filtered_contract_template_ids, invoice_line_ids_filter=invoice_line_ids_filter)

        perc = 0 if value_1 == 0 else round(100*(value_2 - value_1)/float(value_1), 1)

        if perc == 0:
            color = 'oBlack'
        elif stat_types[stat_type]['dir'] == 'up':
            color = 'oGreen' if perc > 0 else 'oRed'
        elif stat_types[stat_type]['dir'] == 'down':
            color = 'oRed' if perc > 0 else 'oGreen'

        result = {
            'value_1': str(value_1) + stat_types[stat_type]['add_symbol'] if add_symbol else value_1,
            'value_2': str(value_2) + stat_types[stat_type]['add_symbol'] if add_symbol else value_2,
            'perc': perc,
            'color': color,
        }
        return result

    def calculate_stat_aggregate(self, stat_type, start_date, end_date, invoice_line_ids_filter=None, filtered_contract_template_ids=None):

        result = 0

        if type(start_date) == str:
            start_date = datetime.strptime(start_date, '%Y-%m-%d')
        if type(end_date) == str:
            end_date = datetime.strptime(end_date, '%Y-%m-%d')

        all_invoice_line_ids = request.env['account.invoice'].search([
            ('date_invoice', '>=', start_date.strftime(DEFAULT_SERVER_DATE_FORMAT)),
            ('date_invoice', '<=', end_date.strftime(DEFAULT_SERVER_DATE_FORMAT)),
        ]).mapped('invoice_line')
        non_recurring_invoice_line_ids = all_invoice_line_ids.filtered(lambda x: not x.asset_category_id)

        # Is this usefull ?
        all_invoice_line_ids = all_invoice_line_ids.filtered(self.get_filter_out_invoice())
        non_recurring_invoice_line_ids = non_recurring_invoice_line_ids.filtered(self.get_filter_out_invoice())

        if invoice_line_ids_filter:
            all_invoice_line_ids = all_invoice_line_ids.filtered(invoice_line_ids_filter)
            recurring_invoice_line_ids = recurring_invoice_line_ids.filtered(invoice_line_ids_filter)

        if filtered_contract_template_ids:
            filter_contract_template = self.get_filter_contract_template(filtered_contract_template_ids)
            all_invoice_line_ids = all_invoice_line_ids.filtered(filter_contract_template)
            non_recurring_invoice_line_ids = non_recurring_invoice_line_ids.filtered(filter_contract_template)

        if stat_type == 'net_revenue':
            # TODO: use @MAT field instead of price_subtotal
            result = sum(all_invoice_line_ids.mapped('price_subtotal'))
            result = int(result)

        elif stat_type == 'nrr':
            # TODO: use @MAT field instead of price_subtotal
            result = sum(non_recurring_invoice_line_ids.mapped('price_subtotal'))
            result = int(result)

        return result

        # Use request.env['account.invoice.line'].read_group([], '', groupby=['create_date:day']) instead
        # for i in range(delta.days):
        #     date = start_date + timedelta(days=i)
        #     value = self.calculate_stat(stat_type, date, filtered_contract_template_ids=filtered_contract_template_ids, invoice_line_ids_filter=invoice_line_ids_filter)
        #     result += value

        # return result

    # @profile  # Used to estimate the cost of each line
    def calculate_stat(self, stat_type, date, filtered_contract_template_ids=None, invoice_line_ids_filter=None):

        if type(date) == str:
            date = datetime.strptime(date, '%Y-%m-%d')

        all_invoice_line_ids = request.env['account.invoice'].search([
            ('date_invoice', '=', date),
        ]).mapped('invoice_line')
        non_recurring_invoice_line_ids = all_invoice_line_ids.filtered(lambda x: not x.asset_category_id)

        # Is this usefull ?
        all_invoice_line_ids = all_invoice_line_ids.filtered(self.get_filter_out_invoice())
        non_recurring_invoice_line_ids = non_recurring_invoice_line_ids.filtered(self.get_filter_out_invoice())

        # grouped by account_id or account_analytic_id ?
        recurring_invoice_line_ids = request.env['account.invoice.line'].search([
            ('asset_start_date', '<=', date),
            ('asset_end_date', '>=', date),
            ('asset_category_id', '!=', None)
        ])

        recurring_invoice_line_ids_1_month_ago = request.env['account.invoice.line'].search([
            ('asset_start_date', '<=', date - relativedelta(months=+1)),
            ('asset_end_date', '>=', date - relativedelta(months=+1)),
            ('asset_category_id', '!=', None)
        ])        # TO FIX: we do not take into account customer invoice --> with mrr negative ?

        # TODO: remove this when mrr only on revenue recognition
        recurring_invoice_line_ids = recurring_invoice_line_ids.filtered(lambda x: x.mrr > 0)

        if invoice_line_ids_filter:
            all_invoice_line_ids = all_invoice_line_ids.filtered(invoice_line_ids_filter)
            recurring_invoice_line_ids = recurring_invoice_line_ids.filtered(invoice_line_ids_filter)
            non_recurring_invoice_line_ids = non_recurring_invoice_line_ids.filtered(invoice_line_ids_filter)

        if filtered_contract_template_ids:
            filter_contract_template = self.get_filter_contract_template(filtered_contract_template_ids)
            all_invoice_line_ids = all_invoice_line_ids.filtered(filter_contract_template)
            recurring_invoice_line_ids = recurring_invoice_line_ids.filtered(filter_contract_template)
            non_recurring_invoice_line_ids = non_recurring_invoice_line_ids.filtered(filter_contract_template)
            recurring_invoice_line_ids_1_month_ago = recurring_invoice_line_ids_1_month_ago.filtered(filter_contract_template)


        def _calculate_logo_churn():

            result = 0

            active_customers_today = recurring_invoice_line_ids.mapped('account_analytic_id')
            active_customers_1_month_ago = recurring_invoice_line_ids_1_month_ago.mapped('account_analytic_id')
            resigned_customers = active_customers_1_month_ago.filtered(lambda x: x not in active_customers_today)

            result = 0 if not active_customers_1_month_ago else len(resigned_customers)/float(len(active_customers_1_month_ago))
            return result

        result = 0

        if stat_type == 'mrr':
            result = sum(recurring_invoice_line_ids.mapped('mrr'))
            result = int(result)

        elif stat_type == 'net_revenue':
            # TODO: use @MAT field instead of price_subtotal
            result = sum(all_invoice_line_ids.mapped('price_subtotal'))
            result = int(result)

        elif stat_type == 'nrr':
            # TODO: use @MAT field instead of price_subtotal
            result = sum(non_recurring_invoice_line_ids.mapped('price_subtotal'))
            result = int(result)


        elif stat_type == 'net_new_mrr' or stat_type == 'revenue_churn':
            new_mrr = 0
            expansion_mrr = 0
            churned_mrr = 0
            net_new_mrr = 0

            # TODO: user filter instead : less search
            invoice_lines_ids_starting_last_month = request.env['account.invoice.line'].search([
                ('asset_category_id', '!=', None),
                ('asset_start_date', '>', (date - relativedelta(months=+1)).strftime(DEFAULT_SERVER_DATE_FORMAT)),
                ('asset_start_date', '<=', date.strftime(DEFAULT_SERVER_DATE_FORMAT)),
            ])
            invoice_lines_ids_stopping_last_month = request.env['account.invoice.line'].search([
                ('asset_category_id', '!=', None),
                ('asset_end_date', '>', (date - relativedelta(months=+1)).strftime(DEFAULT_SERVER_DATE_FORMAT)),
                ('asset_end_date', '<=', date.strftime(DEFAULT_SERVER_DATE_FORMAT)),
            ])

            # DOWN & CANCEL
            for invoice_line in invoice_lines_ids_stopping_last_month:
                # Is there any invoice_line in the next 30 days for this contract ?
                next_invoice_lines = request.env['account.invoice.line'].search([
                    ('asset_category_id', '!=', None),
                    ('asset_start_date', '>=', invoice_line.asset_end_date),
                    ('asset_start_date', '<', (datetime.strptime(invoice_line.asset_end_date, DEFAULT_SERVER_DATE_FORMAT) + relativedelta(months=+1)).strftime(DEFAULT_SERVER_DATE_FORMAT)),
                    ('account_analytic_id', '=', invoice_line.account_analytic_id.id)
                ])
                if next_invoice_lines:
                    next_invoice_line = next_invoice_lines[0]
                    if next_invoice_line.mrr < invoice_line.mrr:
                        churned_mrr += (invoice_line.mrr - next_invoice_line.mrr)
                else:
                    churned_mrr += invoice_line.mrr

            # UP & NEW
            for invoice_line in invoice_lines_ids_starting_last_month:
                # Was there any invoice_line in the last 30 days for this contract ?
                previous_invoice_lines = request.env['account.invoice.line'].search([
                    ('asset_category_id', '!=', None),
                    ('asset_end_date', '<=', invoice_line.asset_start_date),
                    ('asset_end_date', '>', (datetime.strptime(invoice_line.asset_start_date, DEFAULT_SERVER_DATE_FORMAT) - relativedelta(months=+1)).strftime(DEFAULT_SERVER_DATE_FORMAT)),
                    ('account_analytic_id', '=', invoice_line.account_analytic_id.id)
                ])
                if previous_invoice_lines:
                    previous_invoice_lines = previous_invoice_lines[0]
                    # if previous_invoice_lines.mrr > invoice_line.mrr:
                    #     churned_mrr += (invoice_line.mrr - previous_invoice_lines.mrr)
                    if previous_invoice_lines.mrr < invoice_line.mrr:
                        expansion_mrr += (invoice_line.mrr - previous_invoice_lines.mrr)
                else:
                    new_mrr += invoice_line.mrr

            net_new_mrr = new_mrr + expansion_mrr - churned_mrr

            if stat_type == 'net_new_mrr':
                result = new_mrr, expansion_mrr, -churned_mrr, net_new_mrr
            elif stat_type == 'revenue_churn':
                previous_month_mrr = sum(recurring_invoice_line_ids_1_month_ago.mapped('mrr'))
                result = 0 if previous_month_mrr == 0 else (churned_mrr - expansion_mrr)/float(previous_month_mrr)
                result = 100*round(result, 3)

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

        elif stat_type == 'nb_contracts':
            result = len(recurring_invoice_line_ids.mapped('account_analytic_id'))
        else:
            result = 0

        return result
