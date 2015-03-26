# -*- coding: utf-8 -*-
from openerp import http
from openerp.http import request
from dateutil.relativedelta import relativedelta
from datetime import datetime, date, timedelta
from math import floor
import time

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


def get_pruned_tick_values(ticks, nb_desired_ticks):
    nb_values = len(ticks)
    keep_one_of = max(1, floor(nb_values / float(nb_desired_ticks)))

    ticks = [x for x in ticks if x % keep_one_of == 0]

    return ticks


class AccountContractDashboard(http.Controller):

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
            'find_res_id': request.env['ir.model.data'].xmlid_to_res_id,
        })

    @http.route('/account_contract_dashboard/detailed/<string:stat_type>', auth='user', website=True)
    def stats(self, stat_type, **kw):

        contract_templates = request.env['account.analytic.account'].search([('type', '=', 'template')])

        filtered_contract_template_ids = request.httprequest.args.getlist('contract_template_filter') if kw.get('contract_template_filter') else []

        start_date = datetime.strptime(kw.get('start_date'), '%Y-%m-%d') if kw.get('start_date') else default_start_date
        end_date = datetime.strptime(kw.get('end_date'), '%Y-%m-%d') if kw.get('end_date') else default_end_date

        report_name = stat_types[stat_type]['name']

        value_now = self.calculate_stat_diff(stat_type, start_date - relativedelta(months=+1),  end_date - relativedelta(months=+1), start_date, end_date, filtered_contract_template_ids=filtered_contract_template_ids)

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
            # 'value_1_month_ago': value_1_month_ago,
            # 'value_3_months_ago': value_3_months_ago,
            # 'value_12_months_ago': value_12_months_ago,
            'display_stats_by_plan': False if stat_type in ['nrr', 'arpu', 'logo_churn'] else True,
            'currency': '€',
            'rate': compute_rate,
            'href_post_args': href_post_args,
            'find_res_id': request.env['ir.model.data'].xmlid_to_res_id,
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

    @http.route('/account_contract_dashboard/get_stats_history', type="json", auth='user', website=True)
    def get_stats_history(self, stat_type, start_date, end_date, filtered_contract_template_ids=None):

        start_date = datetime.strptime(start_date, '%Y-%m-%d')
        end_date = datetime.strptime(end_date, '%Y-%m-%d')

        results = {}

        results['value_1_month_ago'] = self.calculate_stat_diff(stat_type, start_date - relativedelta(months=+1), end_date - relativedelta(months=+1), start_date - relativedelta(months=+1), end_date - relativedelta(months=+1), filtered_contract_template_ids=filtered_contract_template_ids)
        results['value_3_months_ago'] = self.calculate_stat_diff(stat_type, start_date - relativedelta(months=+3), end_date - relativedelta(months=+3), start_date - relativedelta(months=+3), end_date - relativedelta(months=+3), filtered_contract_template_ids=filtered_contract_template_ids)
        results['value_12_months_ago'] = self.calculate_stat_diff(stat_type, start_date - relativedelta(months=+12), end_date - relativedelta(months=+12), start_date - relativedelta(months=+12), end_date - relativedelta(months=+12), filtered_contract_template_ids=filtered_contract_template_ids)

        return results, stat_types

    @http.route('/account_contract_dashboard/get_stats_by_plan', type="json", auth='user', website=True)
    def get_stats_by_plan(self, stat_type, start_date, end_date, filtered_contract_template_ids=None):

        results = []

        plans = request.env['account.analytic.account'].search([('type', '=', 'template')])

        if filtered_contract_template_ids:
            plans = plans.filtered(lambda x: str(x.id) in filtered_contract_template_ids)

        for plan in plans:
            recurring_invoice_line_ids = request.env['account.invoice.line'].search([
                ('asset_start_date', '<=', end_date),
                ('asset_end_date', '>=', end_date),
                ('asset_category_id', '!=', None),
                ('account_analytic_id.template_id', '=', plan.id),
            ])
            if stat_types[stat_type]['type'] == 'last':
                value = self.calculate_stat(stat_type, end_date, plan=plan)
            elif stat_types[stat_type]['type'] == 'sum':
                value = self.calculate_stat_aggregate(stat_type, start_date, end_date, plan=plan)
            results.append({
                'name': plan.name,
                'nb_customers': len(recurring_invoice_line_ids.mapped('account_analytic_id')),
                'value': value,
            })

        results = sorted((results), key=lambda k: k['value'], reverse=True)

        return results, stat_types

    @http.route('/account_contract_dashboard/calculate_graph_stat', type="json", auth='user', website=True)
    def calculate_graph_stat(self, stat_type, start_date, end_date, filtered_contract_template_ids, complete=False, nb_points=30):

        start_date = datetime.strptime(start_date, '%Y-%m-%d')
        end_date = datetime.strptime(end_date, '%Y-%m-%d')

        delta = end_date - start_date
        ticks = range(delta.days + 1)

        keep_one_of = 1

        if not complete:
            nb_values = len(ticks)
            keep_one_of = max(1, floor(nb_values / float(nb_points)))
            ticks = get_pruned_tick_values(ticks, nb_points)

        results = []

        if stat_type == 'net_revenue':
            request.cr.execute("""
                SELECT s.a, SUM(invoice.amount_total) AS sum
                FROM account_invoice AS invoice, generate_series(%s::timestamp, %s, '%s days') AS s(a)
                WHERE
                    invoice.date_due = s.a AND
                    invoice.type = 'out_invoice' AND
                    invoice.state = 'paid'
                GROUP BY s.a
                ORDER BY s.a
            """, [start_date.strftime(DEFAULT_SERVER_DATETIME_FORMAT), end_date.strftime(DEFAULT_SERVER_DATETIME_FORMAT), 1])
            stat_by_day = request.cr.dictfetchall()
            for k in stat_by_day:
                results.append({
                    '0': k['a'],
                    '1': k['sum'],
                })

        elif stat_type == 'nrr':
            request.cr.execute("""
                SELECT s.a, SUM(line.price_subtotal) AS sum
                FROM account_invoice_line AS line, account_invoice AS invoice, generate_series(%s::timestamp, %s, '%s days') AS s(a)
                WHERE
                    invoice.date_due = s.a AND
                    line.asset_category_id IS NULL AND
                    line.invoice_id = invoice.id AND
                    invoice.type = 'out_invoice' AND
                    invoice.state = 'paid'
                GROUP BY s.a
                ORDER BY s.a
            """, [start_date.strftime(DEFAULT_SERVER_DATETIME_FORMAT), end_date.strftime(DEFAULT_SERVER_DATETIME_FORMAT), 1])
            stat_by_day = request.cr.dictfetchall()
            for k in stat_by_day:
                results.append({
                    '0': k['a'],
                    '1': k['sum'],
                })

        elif stat_type == 'mrr':
            request.cr.execute("""
                SELECT s.a, SUM(line.mrr)
                FROM account_invoice_line AS line, generate_series(%s::timestamp, %s, '%s days') AS s(a)
                WHERE s.a BETWEEN line.asset_start_date AND line.asset_end_date
                GROUP BY s.a
                ORDER BY s.a
            """, [start_date.strftime(DEFAULT_SERVER_DATETIME_FORMAT), end_date.strftime(DEFAULT_SERVER_DATETIME_FORMAT), keep_one_of])
            stat_by_day = request.cr.dictfetchall()
            for k in stat_by_day:
                results.append({
                    '0': k['a'],
                    '1': k['sum'],
                })

        elif stat_type == 'arr':
            request.cr.execute("""
                SELECT s.a, 12*SUM(line.mrr) AS sum
                FROM account_invoice_line AS line, generate_series(%s::timestamp, %s, '%s days') AS s(a)
                WHERE s.a BETWEEN line.asset_start_date AND line.asset_end_date
                GROUP BY s.a
                ORDER BY s.a
            """, [start_date.strftime(DEFAULT_SERVER_DATETIME_FORMAT), end_date.strftime(DEFAULT_SERVER_DATETIME_FORMAT), keep_one_of])
            stat_by_day = request.cr.dictfetchall()
            for k in stat_by_day:
                results.append({
                    '0': k['a'],
                    '1': k['sum'],
                })

        elif stat_type == 'arpu':
            request.cr.execute("""
                SELECT s.a, SUM(line.mrr)/COUNT(DISTINCT line.account_analytic_id) AS sum
                FROM account_invoice_line AS line, generate_series(%s::timestamp, %s, '%s days') AS s(a)
                WHERE s.a BETWEEN line.asset_start_date AND line.asset_end_date
                GROUP BY s.a
                ORDER BY s.a
            """, [start_date.strftime(DEFAULT_SERVER_DATETIME_FORMAT), end_date.strftime(DEFAULT_SERVER_DATETIME_FORMAT), keep_one_of])
            stat_by_day = request.cr.dictfetchall()
            for k in stat_by_day:
                results.append({
                    '0': k['a'],
                    '1': k['sum'],
                })

        elif stat_type == 'nb_contracts':
            request.cr.execute("""
                SELECT s.a, COUNT(DISTINCT line.account_analytic_id) AS sum
                FROM account_invoice_line AS line, generate_series(%s::timestamp, %s, '%s days') AS s(a)
                WHERE s.a BETWEEN line.asset_start_date AND line.asset_end_date
                GROUP BY s.a
                ORDER BY s.a
            """, [start_date.strftime(DEFAULT_SERVER_DATETIME_FORMAT), end_date.strftime(DEFAULT_SERVER_DATETIME_FORMAT), keep_one_of])
            stat_by_day = request.cr.dictfetchall()
            for k in stat_by_day:
                results.append({
                    '0': k['a'],
                    '1': k['sum'],
                })

        elif stat_type == 'logo_churn':
            request.cr.execute("""
                SELECT s.a, COUNT(DISTINCT line.account_analytic_id) AS sum
                FROM account_invoice_line AS line, generate_series(%s::timestamp, %s, '%s days') AS s(a)
                WHERE s.a - interval '30 day' BETWEEN line.asset_start_date AND line.asset_end_date
                GROUP BY s.a
                ORDER BY s.a
            """, [start_date.strftime(DEFAULT_SERVER_DATETIME_FORMAT), end_date.strftime(DEFAULT_SERVER_DATETIME_FORMAT), keep_one_of])
            active_customers_1_month_ago_by_day = request.cr.dictfetchall()
            request.cr.execute("""
                SELECT s.a, COUNT(DISTINCT line.account_analytic_id) AS sum
                FROM account_invoice_line AS line, generate_series(%s::timestamp, %s, '%s days') AS s(a)
                WHERE (s.a - interval '30 day' BETWEEN line.asset_start_date AND line.asset_end_date) AND
                    NOT exists (
                    SELECT 1 from account_invoice_line ail
                    WHERE ail.account_analytic_id = line.account_analytic_id
                    AND (s.a BETWEEN ail.asset_start_date AND ail.asset_end_date)
                    )
                GROUP BY s.a
                ORDER BY s.a
            """, [start_date.strftime(DEFAULT_SERVER_DATETIME_FORMAT), end_date.strftime(DEFAULT_SERVER_DATETIME_FORMAT), keep_one_of])
            resigned_customers_by_day = request.cr.dictfetchall()
            for k in active_customers_1_month_ago_by_day:
                nb_active_1_month_ago = k['sum']
                # Find the corresponding nb_resigned at the same date
                nb_resigned = next((d['sum'] for d in resigned_customers_by_day if k['a'] == d['a']), 0)
                results.append({
                    '0': k['a'],
                    '1': 0 if not nb_active_1_month_ago else 100*nb_resigned/float(nb_active_1_month_ago),
                })

        elif stat_type == 'ltv':
            start_time = time.time()
            request.cr.execute("""
                SELECT s.a, COUNT(DISTINCT line.account_analytic_id) AS sum
                FROM account_invoice_line AS line, generate_series(%s::timestamp, %s, '%s days') AS s(a)
                WHERE s.a - interval '30 day' BETWEEN line.asset_start_date AND line.asset_end_date
                GROUP BY s.a
                ORDER BY s.a
            """, [start_date.strftime(DEFAULT_SERVER_DATETIME_FORMAT), end_date.strftime(DEFAULT_SERVER_DATETIME_FORMAT), keep_one_of])
            active_customers_1_month_ago_by_day = request.cr.dictfetchall()
            request.cr.execute("""
                SELECT s.a, COUNT(DISTINCT line.account_analytic_id) AS sum
                FROM account_invoice_line AS line, generate_series(%s::timestamp, %s, '%s days') AS s(a)
                WHERE (s.a - interval '30 day' BETWEEN line.asset_start_date AND line.asset_end_date) AND
                    NOT exists (
                    SELECT 1 from account_invoice_line ail
                    WHERE ail.account_analytic_id = line.account_analytic_id
                    AND (s.a BETWEEN ail.asset_start_date AND ail.asset_end_date)
                    )
                GROUP BY s.a
                ORDER BY s.a
            """, [start_date.strftime(DEFAULT_SERVER_DATETIME_FORMAT), end_date.strftime(DEFAULT_SERVER_DATETIME_FORMAT), keep_one_of])
            resigned_customers_by_day = request.cr.dictfetchall()

            request.cr.execute("""
                SELECT s.a, SUM(line.mrr)/COUNT(DISTINCT line.account_analytic_id) AS sum
                FROM account_invoice_line AS line, generate_series(%s::timestamp, %s, '%s days') AS s(a)
                WHERE s.a BETWEEN line.asset_start_date AND line.asset_end_date
                GROUP BY s.a
                ORDER BY s.a
            """, [start_date.strftime(DEFAULT_SERVER_DATETIME_FORMAT), end_date.strftime(DEFAULT_SERVER_DATETIME_FORMAT), keep_one_of])
            arpu_by_day = request.cr.dictfetchall()

            for k in active_customers_1_month_ago_by_day:
                nb_active_1_month_ago = k['sum']
                # Find the corresponding nb_resigned at the same date
                nb_resigned = next((d['sum'] for d in resigned_customers_by_day if k['a'] == d['a']), 0)

                logo_churn = 0 if not nb_active_1_month_ago else nb_resigned/float(nb_active_1_month_ago)

                avg_mrr_per_customer = next((d['sum'] for d in arpu_by_day if k['a'] == d['a']), 0)
                results.append({
                    '0': k['a'],
                    '1': 0 if not logo_churn else avg_mrr_per_customer / float(logo_churn),
                })
        else:
            for i in ticks:

                # METHOD NON-OPTIMIZED

                date = start_date + timedelta(days=i)
                value = self.calculate_stat(stat_type, date, filtered_contract_template_ids=filtered_contract_template_ids)
                results.append({
                    '0': str(date).split(' ')[0],
                    '1': value,
                })

        return stat_types[stat_type]['name'], results

    @http.route('/account_contract_dashboard/calculate_graph_mrr_growth', type="json", auth='user', website=True)
    def calculate_graph_mrr_growth(self, start_date, end_date, filtered_contract_template_ids):

        # THIS IS ROLLING MONTH CALCULATION
        complete = False
        nb_points = 30

        start_date = datetime.strptime(start_date, '%Y-%m-%d')
        end_date = datetime.strptime(end_date, '%Y-%m-%d')

        delta = end_date - start_date
        ticks = range(delta.days + 1)

        if not complete:
            ticks = get_pruned_tick_values(ticks, nb_points)

        results = [[], [], [], []]

        # Use request.env['account.invoice.line'].read_group([], '', groupby=['create_date:day']) instead
        for i in ticks:
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

    def calculate_stat_diff(self, stat_type, start_date_1, end_date_1, start_date_2, end_date_2, add_symbol=False, filtered_contract_template_ids=None):

        if stat_types[stat_type]['type'] == 'last':
            value_1 = self.calculate_stat(stat_type, end_date_1, filtered_contract_template_ids=filtered_contract_template_ids)
            value_2 = self.calculate_stat(stat_type, end_date_2, filtered_contract_template_ids=filtered_contract_template_ids)
        elif stat_types[stat_type]['type'] == 'sum':
            # If sum, we aggregate all values between start_date and end_date
            value_1 = self.calculate_stat_aggregate(stat_type, start_date_1, end_date_1, filtered_contract_template_ids=filtered_contract_template_ids)
            value_2 = self.calculate_stat_aggregate(stat_type, start_date_2, end_date_2, filtered_contract_template_ids=filtered_contract_template_ids)

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

    def calculate_stat_aggregate(self, stat_type, start_date, end_date, plan=None, filtered_contract_template_ids=None):

        result = 0

        if type(start_date) == str:
            start_date = datetime.strptime(start_date, '%Y-%m-%d')
        if type(end_date) == str:
            end_date = datetime.strptime(end_date, '%Y-%m-%d')

        if stat_type == 'net_revenue':
            request.cr.execute("""
                SELECT SUM(invoice.amount_total) AS sum
                FROM account_invoice AS invoice
                WHERE
                    (invoice.date_due BETWEEN %s AND %s) AND
                    invoice.type = 'out_invoice' AND
                    invoice.state = 'paid'
            """, [start_date.strftime(DEFAULT_SERVER_DATETIME_FORMAT), end_date.strftime(DEFAULT_SERVER_DATETIME_FORMAT)])
            sql_results = request.cr.dictfetchall()
            result = 0 if not sql_results or not sql_results[0]['sum'] else int(sql_results[0]['sum'])

        elif stat_type == 'nrr':
            request.cr.execute("""
                SELECT SUM(line.price_subtotal) AS sum
                FROM account_invoice_line AS line, account_invoice AS invoice
                WHERE
                    (invoice.date_due BETWEEN %s AND %s) AND
                    line.asset_category_id IS NULL AND
                    line.invoice_id = invoice.id AND
                    invoice.type = 'out_invoice' AND
                    invoice.state = 'paid'
            """, [start_date.strftime(DEFAULT_SERVER_DATETIME_FORMAT), end_date.strftime(DEFAULT_SERVER_DATETIME_FORMAT)])
            sql_results = request.cr.dictfetchall()
            result = 0 if not sql_results or not sql_results[0]['sum'] else int(sql_results[0]['sum'])

        return result

        # Use request.env['account.invoice.line'].read_group([], '', groupby=['create_date:day']) instead
        # for i in range(delta.days):
        #     date = start_date + timedelta(days=i)
        #     value = self.calculate_stat(stat_type, date, filtered_contract_template_ids=filtered_contract_template_ids, invoice_line_ids_filter=invoice_line_ids_filter)
        #     result += value

        # return result

    # @profile  # Used to estimate the cost of each line
    def calculate_stat(self, stat_type, date, filtered_contract_template_ids=None, plan=None):

        if type(date) == str:
            date = datetime.strptime(date, '%Y-%m-%d')

        shared_domain = [
            ('asset_category_id', '!=', None)
        ]
        if plan:
            shared_domain.append(('account_analytic_id.template_id', '=', plan.id))
        elif filtered_contract_template_ids:
            shared_domain.append(('account_analytic_id.template_id', 'in', [int(ids) for ids in filtered_contract_template_ids]))

        recurring_invoice_line_ids = request.env['account.invoice.line'].search(
            shared_domain + [
                ('asset_start_date', '<=', date),
                ('asset_end_date', '>=', date),
            ]
        )

        recurring_invoice_line_ids_1_month_ago = request.env['account.invoice.line'].search(
            shared_domain + [
                ('asset_start_date', '<=', date - relativedelta(months=+1)),
                ('asset_end_date', '>=', date - relativedelta(months=+1)),
            ]
        )

        def _get_nb_contracts(date):
            request.cr.execute("""
                SELECT COUNT(DISTINCT line.account_analytic_id) AS sum
                FROM account_invoice_line AS line
                WHERE date %s BETWEEN line.asset_start_date AND line.asset_end_date
            """, [date.strftime(DEFAULT_SERVER_DATE_FORMAT)])
            nb_contracts = request.cr.dictfetchall()
            return 0 if not nb_contracts or not nb_contracts[0]['sum'] else nb_contracts[0]['sum']

        def _get_mrr(date):
            request.cr.execute("""
                SELECT SUM(line.mrr) AS sum
                FROM account_invoice_line AS line
                WHERE date %s BETWEEN line.asset_start_date AND line.asset_end_date
            """, [date.strftime(DEFAULT_SERVER_DATE_FORMAT)])
            mrr = request.cr.dictfetchall()
            return 0 if not mrr or not mrr[0]['sum'] else mrr[0]['sum']

        def _calculate_logo_churn(date):
            request.cr.execute("""
                SELECT COUNT(DISTINCT line.account_analytic_id) AS sum
                FROM account_invoice_line AS line
                WHERE date %s - interval '30 day' BETWEEN line.asset_start_date AND line.asset_end_date
            """, [date.strftime(DEFAULT_SERVER_DATETIME_FORMAT)])
            sql_results = request.cr.dictfetchall()
            active_customers_1_month_ago = 0 if not sql_results or not sql_results[0]['sum'] else sql_results[0]['sum']
            request.cr.execute("""
                SELECT COUNT(DISTINCT line.account_analytic_id) AS sum
                FROM account_invoice_line AS line
                WHERE (date %s - interval '30 day' BETWEEN line.asset_start_date AND line.asset_end_date) AND
                    NOT exists (
                    SELECT 1 from account_invoice_line ail
                    WHERE ail.account_analytic_id = line.account_analytic_id
                    AND (date %s BETWEEN ail.asset_start_date AND ail.asset_end_date)
                    )
            """, [date.strftime(DEFAULT_SERVER_DATETIME_FORMAT), date.strftime(DEFAULT_SERVER_DATETIME_FORMAT)])
            sql_results = request.cr.dictfetchall()
            resigned_customers = 0 if not sql_results or not sql_results[0]['sum'] else sql_results[0]['sum']

            return 0 if not active_customers_1_month_ago else resigned_customers/float(active_customers_1_month_ago)

        result = 0

        if stat_type == 'mrr':
            result = _get_mrr(date)
            result = int(result)

        # TO IMPROVE
        elif stat_type == 'net_new_mrr' or stat_type == 'revenue_churn':
            new_mrr = 0
            expansion_mrr = 0
            churned_mrr = 0
            net_new_mrr = 0

            request.cr.execute("""
                SELECT COUNT(DISTINCT line.account_analytic_id) AS sum
                FROM account_invoice_line AS line
                WHERE (date %s - interval '30 day' BETWEEN line.asset_start_date AND line.asset_end_date) AND
                    NOT exists (
                    SELECT 1 from account_invoice_line ail
                    WHERE ail.account_analytic_id = line.account_analytic_id
                    AND (date %s BETWEEN ail.asset_start_date AND ail.asset_end_date)
                    )
            """, [date.strftime(DEFAULT_SERVER_DATETIME_FORMAT), date.strftime(DEFAULT_SERVER_DATETIME_FORMAT)])
            sql_results = request.cr.dictfetchall()
            new_mrr = 0 if not sql_results or not sql_results[0]['sum'] else sql_results[0]['sum']



            invoice_line_ids_starting_last_month = request.env['account.invoice.line'].search(
                shared_domain + [
                    ('asset_start_date', '>', (date - relativedelta(months=+1)).strftime(DEFAULT_SERVER_DATE_FORMAT)),
                    ('asset_start_date', '<=', date.strftime(DEFAULT_SERVER_DATE_FORMAT)),
                ]
            )
            invoice_lines_ids_stopping_last_month = request.env['account.invoice.line'].search(
                shared_domain + [
                    ('asset_end_date', '>', (date - relativedelta(months=+1)).strftime(DEFAULT_SERVER_DATE_FORMAT)),
                    ('asset_end_date', '<=', date.strftime(DEFAULT_SERVER_DATE_FORMAT)),
                ]
            )

            # DOWN & CANCEL
            for invoice in invoice_lines_ids_stopping_last_month.mapped('invoice_id'):

                invoice_line_ids = invoice_lines_ids_stopping_last_month.filtered(lambda x: x.invoice_id == invoice)
                invoice_line = invoice_line_ids[0]

                if not invoice_line:
                    continue
                # Is there any invoice_line in the next 30 days for this contract ?
                next_invoice_line_ids = request.env['account.invoice.line'].search(
                    shared_domain + [
                        ('asset_start_date', '>=', invoice_line.asset_end_date),
                        ('asset_start_date', '<', (datetime.strptime(invoice_line.asset_end_date, DEFAULT_SERVER_DATE_FORMAT) + relativedelta(months=+1)).strftime(DEFAULT_SERVER_DATE_FORMAT)),
                        ('account_analytic_id', '=', invoice_line.account_analytic_id.id)
                    ]
                )
                previous_mrr = sum([x['mrr'] for x in invoice_line_ids.read(['mrr'])])

                if next_invoice_line_ids:
                    next_mrr = sum([x['mrr'] for x in next_invoice_line_ids.read(['mrr'])])
                    if next_mrr < previous_mrr:
                        # DOWN
                        churned_mrr += (previous_mrr - next_mrr)
                else:
                    # CANCEL
                    churned_mrr += previous_mrr

            # UP & NEW
            for invoice in invoice_line_ids_starting_last_month.mapped('invoice_id'):

                invoice_line_ids = invoice_line_ids_starting_last_month.filtered(lambda x: x.invoice_id == invoice)
                invoice_line = invoice_line_ids[0]

                if not invoice_line:
                    continue

                # Was there any invoice_line in the last 30 days for this contract ?
                previous_invoice_line_ids = request.env['account.invoice.line'].search(shared_domain + [
                        ('asset_end_date', '<=', invoice_line.asset_start_date),
                        ('asset_end_date', '>', (datetime.strptime(invoice_line.asset_start_date, DEFAULT_SERVER_DATE_FORMAT) - relativedelta(months=+1)).strftime(DEFAULT_SERVER_DATE_FORMAT)),
                        ('account_analytic_id', '=', invoice_line.account_analytic_id.id)]
                )
                next_mrr = sum([x['mrr'] for x in invoice_line_ids.read(['mrr'])])
                if previous_invoice_line_ids:
                    previous_mrr = sum([x['mrr'] for x in previous_invoice_line_ids.read(['mrr'])])

                    if previous_mrr < next_mrr:
                        # UP
                        expansion_mrr += (next_mrr - previous_mrr)
                else:
                    # NEW
                    new_mrr += next_mrr

            net_new_mrr = new_mrr + expansion_mrr - churned_mrr

            if stat_type == 'net_new_mrr':
                result = new_mrr, expansion_mrr, -churned_mrr, net_new_mrr
            elif stat_type == 'revenue_churn':
                previous_month_mrr = _get_mrr((date - relativedelta(months=+1)))
                result = 0 if previous_month_mrr == 0 else (churned_mrr - expansion_mrr)/float(previous_month_mrr)
                result = 100*round(result, 3)

        elif stat_type == 'arpu':
            mrr = _get_mrr(date)
            nb_customers = _get_nb_contracts(date)
            result = 0 if not nb_customers else mrr/float(nb_customers)
            result = int(result)

        elif stat_type == 'arr':
            result = 12*_get_mrr(date)
            result = int(result)

        elif stat_type == 'ltv':
            # LTV = Average Monthly Recurring Revenue Per Customer ÷ User Churn Rate
            mrr = _get_mrr(date)
            nb_contracts = _get_nb_contracts(date)
            avg_mrr_per_customer = 0 if nb_contracts == 0 else mrr / float(nb_contracts)
            logo_churn = _calculate_logo_churn(date)
            result = 0 if logo_churn == 0 else avg_mrr_per_customer/float(logo_churn)
            result = int(result)

        elif stat_type == 'logo_churn':
            result = 100*_calculate_logo_churn(date)
            result = round(result, 1)

        elif stat_type == 'nb_contracts':
            result = _get_nb_contracts(date)
        else:
            result = 0

        return result
