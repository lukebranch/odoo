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

        filtered_contract_template_ids = request.httprequest.args.getlist('contract_template_filter') if kw.get('contract_template_filter') else []

        start_date = datetime.strptime(kw.get('start_date'), '%Y-%m-%d') if kw.get('start_date') else default_start_date
        end_date = datetime.strptime(kw.get('end_date'), '%Y-%m-%d') if kw.get('end_date') else default_end_date

        value_now = self.calculate_stat_diff(
            stat_type,
            start_date - relativedelta(months=+1),
            end_date - relativedelta(months=+1),
            start_date,
            end_date,
            filtered_contract_template_ids=filtered_contract_template_ids
        )

        href_post_args = 'start_date=%s&end_date=%s&' % (start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d'))
        for item in filtered_contract_template_ids:
            href_post_args += 'contract_template_filter=%s&' % item

        return http.request.render('account_contract_dashboard.detailed_dashboard', {
            'all_stats': stat_types,
            'stat_type': stat_type,
            'contract_templates': request.env['account.analytic.account'].search([('type', '=', 'template')]),
            'filtered_contract_template_ids': filtered_contract_template_ids,
            'currency': '€',
            'report_name': stat_types[stat_type]['name'],
            'start_date': start_date.strftime('%Y-%m-%d'),
            'end_date': end_date.strftime('%Y-%m-%d'),
            'value_now': value_now,
            'display_stats_by_plan': False if stat_type in ['nrr', 'arpu', 'logo_churn'] else True,
            'currency': '€',
            'href_post_args': href_post_args,
            'find_res_id': request.env['ir.model.data'].xmlid_to_res_id,
        })

    @http.route('/account_contract_dashboard/forecast', auth='user', website=True)
    def forecast(self, **kw):

        return http.request.render('account_contract_dashboard.forecast', {
            'currency': request.env['res.company'].search([])[0].currency_id.symbol,
        })

    @http.route('/account_contract_dashboard/get_default_values_forecast', type="json", auth='user', website=True)
    def get_default_values_forecast(self, forecast_type=None, end_date=None):

        print("end_Date")
        print(end_date)
        if not end_date:
            end_date = date.today()
        mrr = self.calculate_stat('mrr', end_date)
        net_new_mrr = self.calculate_stat('net_new_mrr', end_date)[3]
        revenue_churn = self.calculate_stat('revenue_churn', end_date)
        nb_contracts = self.calculate_stat('nb_contracts', end_date)
        arpu = self.calculate_stat('arpu', end_date)

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

        results['value_1_month_ago'] = self.calculate_stat_diff(
            stat_type, start_date - relativedelta(months=+1),
            end_date - relativedelta(months=+1),
            start_date - relativedelta(months=+1),
            end_date - relativedelta(months=+1),
            filtered_contract_template_ids=filtered_contract_template_ids)

        results['value_3_months_ago'] = self.calculate_stat_diff(
            stat_type,
            start_date - relativedelta(months=+3),
            end_date - relativedelta(months=+3),
            start_date - relativedelta(months=+3),
            end_date - relativedelta(months=+3),
            filtered_contract_template_ids=filtered_contract_template_ids)

        results['value_12_months_ago'] = self.calculate_stat_diff(
            stat_type,
            start_date - relativedelta(months=+12),
            end_date - relativedelta(months=+12),
            start_date - relativedelta(months=+12),
            end_date - relativedelta(months=+12),
            filtered_contract_template_ids=filtered_contract_template_ids)

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
                value = self.calculate_stat(stat_type, end_date, filtered_contract_template_ids=[plan.id])
            elif stat_types[stat_type]['type'] == 'sum':
                value = self.calculate_stat_aggregate(stat_type, start_date, end_date, filtered_contract_template_ids=[plan.id])
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

        ticks = range(delta.days + 1) if complete else get_pruned_tick_values(range(delta.days + 1), nb_points)

        results = []

        for i in ticks:
            # METHOD NON-OPTIMIZED (see previous commit for optimized calls)
            date = start_date + timedelta(days=i)
            if stat_types[stat_type]['type'] == 'last':
                value = self.calculate_stat(stat_type, date, filtered_contract_template_ids=filtered_contract_template_ids)
            elif stat_types[stat_type]['type'] == 'sum':
                value = self.calculate_stat_aggregate(stat_type, date, date, filtered_contract_template_ids=filtered_contract_template_ids)

            results.append({
                '0': str(date).split(' ')[0],
                '1': value,
            })

        return stat_types[stat_type]['name'], results

    @http.route('/account_contract_dashboard/calculate_graph_mrr_growth', type="json", auth='user', website=True)
    def calculate_graph_mrr_growth(self, start_date, end_date, filtered_contract_template_ids, complete=False, nb_points=30):

        # THIS IS ROLLING MONTH CALCULATION

        start_date = datetime.strptime(start_date, '%Y-%m-%d')
        end_date = datetime.strptime(end_date, '%Y-%m-%d')
        delta = end_date - start_date

        ticks = range(delta.days + 1) if complete else get_pruned_tick_values(range(delta.days + 1), nb_points)

        results = [[], [], [], []]

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
    def calculate_stats_diff_30_days_ago(self, stat_type, start_date, end_date, filtered_contract_template_ids):

        results = {}

        # Used in global dashboard
        if type(start_date) == str:
            start_date = datetime.strptime(start_date, '%Y-%m-%d')
        if type(end_date) == str:
            end_date = datetime.strptime(end_date, '%Y-%m-%d')
        start_date_1 = start_date - relativedelta(months=+1)
        end_date_1 = end_date - relativedelta(months=+1)
        start_date_2 = start_date
        end_date_2 = end_date

        results = self.calculate_stat_diff(
            stat_type,
            start_date_1,
            end_date_1,
            start_date_2,
            end_date_2,
            add_symbol=True,
            filtered_contract_template_ids=filtered_contract_template_ids)

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

    def calculate_stat_aggregate(self, stat_type, start_date, end_date, filtered_contract_template_ids=None):

        result = 0

        if type(start_date) == str:
            start_date = datetime.strptime(start_date, '%Y-%m-%d')
        if type(end_date) == str:
            end_date = datetime.strptime(end_date, '%Y-%m-%d')

        if stat_type == 'net_revenue':
            if not filtered_contract_template_ids:
                request.cr.execute("""
                    SELECT SUM(line.price_subtotal) AS sum
                    FROM account_invoice_line AS line, account_invoice AS invoice
                    WHERE
                        (invoice.date_due BETWEEN %s AND %s) AND
                        line.invoice_id = invoice.id AND
                        invoice.type IN ('out_invoice') AND
                        invoice.state NOT IN ('draft', 'cancel')
                """, [start_date.strftime(DEFAULT_SERVER_DATETIME_FORMAT), end_date.strftime(DEFAULT_SERVER_DATETIME_FORMAT)])
            else:
                request.cr.execute("""
                    SELECT SUM(line.price_subtotal) AS sum
                    FROM account_invoice_line AS line, account_invoice AS invoice, account_analytic_account AS analytic_account
                    WHERE
                        (invoice.date_due BETWEEN %s AND %s) AND
                        line.invoice_id = invoice.id AND
                        invoice.type IN ('out_invoice') AND
                        invoice.state NOT IN ('draft', 'cancel') AND
                        line.account_analytic_id = analytic_account.id AND
                        analytic_account.template_id IN %s
                """, [start_date.strftime(DEFAULT_SERVER_DATETIME_FORMAT), end_date.strftime(DEFAULT_SERVER_DATETIME_FORMAT), tuple(filtered_contract_template_ids)])
            sql_results = request.cr.dictfetchall()
            result = 0 if not sql_results or not sql_results[0]['sum'] else int(sql_results[0]['sum'])

        elif stat_type == 'nrr':
            if not filtered_contract_template_ids:
                request.cr.execute("""
                    SELECT SUM(line.price_subtotal) AS sum
                    FROM account_invoice_line AS line, account_invoice AS invoice
                    WHERE
                        (invoice.date_due BETWEEN %s AND %s) AND
                        line.asset_category_id IS NULL AND
                        line.invoice_id = invoice.id AND
                        invoice.type IN ('out_invoice') AND
                        invoice.state NOT IN ('draft', 'cancel')
                """, [start_date.strftime(DEFAULT_SERVER_DATETIME_FORMAT), end_date.strftime(DEFAULT_SERVER_DATETIME_FORMAT)])
            else:
                request.cr.execute("""
                    SELECT SUM(line.price_subtotal) AS sum
                    FROM account_invoice_line AS line, account_invoice AS invoice, account_analytic_account AS analytic_account
                    WHERE
                        (invoice.date_due BETWEEN %s AND %s) AND
                        line.asset_category_id IS NULL AND
                        line.invoice_id = invoice.id AND
                        invoice.type IN ('out_invoice') AND
                        invoice.state NOT IN ('draft', 'cancel') AND
                        line.account_analytic_id = analytic_account.id AND
                        analytic_account.template_id IN %s
                """, [start_date.strftime(DEFAULT_SERVER_DATETIME_FORMAT), end_date.strftime(DEFAULT_SERVER_DATETIME_FORMAT), tuple(filtered_contract_template_ids)])
            sql_results = request.cr.dictfetchall()
            result = 0 if not sql_results or not sql_results[0]['sum'] else int(sql_results[0]['sum'])

        return result

    def calculate_stat(self, stat_type, date, filtered_contract_template_ids=None):

        if type(date) == str:
            date = datetime.strptime(date, '%Y-%m-%d')

        def _calculate_nb_contracts(date):
            if not filtered_contract_template_ids:
                request.cr.execute("""
                    SELECT COUNT(DISTINCT line.account_analytic_id) AS sum
                    FROM account_invoice_line AS line, account_invoice AS invoice
                    WHERE (date %s BETWEEN line.asset_start_date AND line.asset_end_date) AND
                        invoice.id = line.invoice_id AND
                        invoice.type IN ('out_invoice') AND
                        invoice.state NOT IN ('draft', 'cancel')
                """, [date.strftime(DEFAULT_SERVER_DATE_FORMAT)])
            else:
                request.cr.execute("""
                    SELECT COUNT(DISTINCT line.account_analytic_id) AS sum
                    FROM account_invoice_line AS line, account_invoice AS invoice, account_analytic_account AS analytic_account
                    WHERE (date %s BETWEEN line.asset_start_date AND line.asset_end_date) AND
                        invoice.id = line.invoice_id AND
                        invoice.type IN ('out_invoice') AND
                        invoice.state NOT IN ('draft', 'cancel') AND
                        line.account_analytic_id = analytic_account.id AND
                        analytic_account.template_id IN %s
                """, [date.strftime(DEFAULT_SERVER_DATE_FORMAT), tuple(filtered_contract_template_ids)])
            nb_contracts = request.cr.dictfetchall()
            return 0 if not nb_contracts or not nb_contracts[0]['sum'] else nb_contracts[0]['sum']

        def _calculate_mrr(date):
            if not filtered_contract_template_ids:
                request.cr.execute("""
                    SELECT SUM(line.mrr) AS sum
                    FROM account_invoice_line AS line, account_invoice AS invoice
                    WHERE date %s BETWEEN line.asset_start_date AND line.asset_end_date AND
                        invoice.id = line.invoice_id AND
                        invoice.type IN ('out_invoice') AND
                        invoice.state NOT IN ('draft', 'cancel')
                """, [date.strftime(DEFAULT_SERVER_DATE_FORMAT)])
            else:
                request.cr.execute("""
                    SELECT SUM(line.mrr) AS sum
                    FROM account_invoice_line AS line, account_invoice AS invoice, account_analytic_account AS analytic_account
                    WHERE date %s BETWEEN line.asset_start_date AND line.asset_end_date AND
                        invoice.id = line.invoice_id AND
                        invoice.type IN ('out_invoice') AND
                        invoice.state NOT IN ('draft', 'cancel') AND
                        line.account_analytic_id = analytic_account.id AND
                        analytic_account.template_id IN %s
                """, [date.strftime(DEFAULT_SERVER_DATE_FORMAT), tuple(filtered_contract_template_ids)])
            mrr = request.cr.dictfetchall()
            return 0 if not mrr or not mrr[0]['sum'] else mrr[0]['sum']

        def _calculate_logo_churn(date):
            if not filtered_contract_template_ids:
                request.cr.execute("""
                    SELECT COUNT(DISTINCT line.account_analytic_id) AS sum
                    FROM account_invoice_line AS line, account_invoice AS invoice
                    WHERE date %s - interval '1 months' BETWEEN line.asset_start_date AND line.asset_end_date AND
                        invoice.id = line.invoice_id AND
                        invoice.type IN ('out_invoice') AND
                        invoice.state NOT IN ('draft', 'cancel')
                """, [date.strftime(DEFAULT_SERVER_DATETIME_FORMAT)])
            else:
                request.cr.execute("""
                    SELECT COUNT(DISTINCT line.account_analytic_id) AS sum
                    FROM account_invoice_line AS line, account_invoice AS invoice, account_analytic_account AS analytic_account
                    WHERE date %s - interval '1 months' BETWEEN line.asset_start_date AND line.asset_end_date AND
                        invoice.id = line.invoice_id AND
                        invoice.type IN ('out_invoice') AND
                        invoice.state NOT IN ('draft', 'cancel') AND
                        line.account_analytic_id = analytic_account.id AND
                        analytic_account.template_id IN %s
                """, [date.strftime(DEFAULT_SERVER_DATETIME_FORMAT), tuple(filtered_contract_template_ids)])
            sql_results = request.cr.dictfetchall()
            active_customers_1_month_ago = 0 if not sql_results or not sql_results[0]['sum'] else sql_results[0]['sum']
            if not filtered_contract_template_ids:
                request.cr.execute("""
                    SELECT COUNT(DISTINCT line.account_analytic_id) AS sum
                    FROM account_invoice_line AS line, account_invoice AS invoice
                    WHERE (date %s - interval '1 months' BETWEEN line.asset_start_date AND line.asset_end_date) AND
                        invoice.id = line.invoice_id AND
                        invoice.type IN ('out_invoice') AND
                        invoice.state NOT IN ('draft', 'cancel') AND
                        NOT exists (
                        SELECT 1 from account_invoice_line ail
                        WHERE ail.account_analytic_id = line.account_analytic_id
                        AND (date %s BETWEEN ail.asset_start_date AND ail.asset_end_date)
                        )
                """, [date.strftime(DEFAULT_SERVER_DATETIME_FORMAT), date.strftime(DEFAULT_SERVER_DATETIME_FORMAT)])
            else:
                request.cr.execute("""
                    SELECT COUNT(DISTINCT line.account_analytic_id) AS sum
                    FROM account_invoice_line AS line, account_invoice AS invoice, account_analytic_account AS analytic_account
                    WHERE (date %s - interval '1 months' BETWEEN line.asset_start_date AND line.asset_end_date) AND
                        invoice.id = line.invoice_id AND
                        invoice.type IN ('out_invoice') AND
                        invoice.state NOT IN ('draft', 'cancel') AND
                        line.account_analytic_id = analytic_account.id AND
                        analytic_account.template_id IN %s AND
                        NOT exists (
                        SELECT 1 from account_invoice_line ail
                        WHERE ail.account_analytic_id = line.account_analytic_id
                        AND (date %s BETWEEN ail.asset_start_date AND ail.asset_end_date)
                        )
                """, [date.strftime(DEFAULT_SERVER_DATETIME_FORMAT), tuple(filtered_contract_template_ids), date.strftime(DEFAULT_SERVER_DATETIME_FORMAT)])
            sql_results = request.cr.dictfetchall()
            resigned_customers = 0 if not sql_results or not sql_results[0]['sum'] else sql_results[0]['sum']

            return 0 if not active_customers_1_month_ago else resigned_customers/float(active_customers_1_month_ago)

        def _calculate_revenue_churn(date):
            if not filtered_contract_template_ids:
                request.cr.execute("""
                    SELECT SUM(line.mrr) AS sum
                    FROM account_invoice_line AS line, account_invoice AS invoice
                    WHERE (date %s - interval '1 months' BETWEEN line.asset_start_date AND line.asset_end_date) AND
                        invoice.id = line.invoice_id AND
                        invoice.type IN ('out_invoice') AND
                        invoice.state NOT IN ('draft', 'cancel') AND
                        NOT exists (
                        SELECT 1 from account_invoice_line ail
                        WHERE ail.account_analytic_id = line.account_analytic_id
                        AND (date %s BETWEEN ail.asset_start_date AND ail.asset_end_date)
                        )
                """, [date.strftime(DEFAULT_SERVER_DATETIME_FORMAT), date.strftime(DEFAULT_SERVER_DATETIME_FORMAT)])
            else:
                request.cr.execute("""
                    SELECT SUM(line.mrr) AS sum
                    FROM account_invoice_line AS line, account_invoice AS invoice, account_analytic_account AS analytic_account
                    WHERE (date %s - interval '1 months' BETWEEN line.asset_start_date AND line.asset_end_date) AND
                        invoice.id = line.invoice_id AND
                        invoice.type IN ('out_invoice') AND
                        invoice.state NOT IN ('draft', 'cancel') AND
                        line.account_analytic_id = analytic_account.id AND
                        analytic_account.template_id IN %s AND
                        NOT exists (
                        SELECT 1 from account_invoice_line ail
                        WHERE ail.account_analytic_id = line.account_analytic_id
                        AND (date %s BETWEEN ail.asset_start_date AND ail.asset_end_date)
                        )
                """, [date.strftime(DEFAULT_SERVER_DATETIME_FORMAT), tuple(filtered_contract_template_ids), date.strftime(DEFAULT_SERVER_DATETIME_FORMAT)])
            sql_results = request.cr.dictfetchall()
            churned_mrr = 0 if not sql_results or not sql_results[0]['sum'] else sql_results[0]['sum']

            previous_month_mrr = _calculate_mrr((date - relativedelta(months=+1)))
            result = 0 if previous_month_mrr == 0 else (churned_mrr)/float(previous_month_mrr)

            return result

        result = 0

        if stat_type == 'mrr':
            result = _calculate_mrr(date)
            result = int(result)

        # TO IMPROVE

        elif stat_type == 'revenue_churn':
            result = _calculate_revenue_churn(date)
            result = 100*round(result, 3)

        elif stat_type == 'arpu':
            mrr = _calculate_mrr(date)
            nb_customers = _calculate_nb_contracts(date)
            result = 0 if not nb_customers else mrr/float(nb_customers)
            result = int(result)

        elif stat_type == 'arr':
            result = 12*_calculate_mrr(date)
            result = int(result)

        elif stat_type == 'ltv':
            # LTV = Average Monthly Recurring Revenue Per Customer / User Churn Rate
            mrr = _calculate_mrr(date)
            nb_contracts = _calculate_nb_contracts(date)
            avg_mrr_per_customer = 0 if nb_contracts == 0 else mrr / float(nb_contracts)
            logo_churn = _calculate_logo_churn(date)
            result = 0 if logo_churn == 0 else avg_mrr_per_customer/float(logo_churn)
            result = int(result)

        elif stat_type == 'logo_churn':
            result = 100*_calculate_logo_churn(date)
            result = round(result, 1)

        elif stat_type == 'nb_contracts':
            result = _calculate_nb_contracts(date)

        elif stat_type == 'net_new_mrr':
            new_mrr = 0
            expansion_mrr = 0
            down_mrr = 0
            cancel_mrr = 0
            churned_mrr = 0
            net_new_mrr = 0

            # 1. NEW
            if not filtered_contract_template_ids:
                request.cr.execute("""
                    SELECT SUM(line.mrr) AS sum
                    FROM account_invoice_line AS line, account_invoice AS invoice
                    WHERE (date %s BETWEEN line.asset_start_date AND line.asset_end_date) AND
                        invoice.id = line.invoice_id AND
                        invoice.type IN ('out_invoice') AND
                        invoice.state NOT IN ('draft', 'cancel') AND
                        NOT exists (
                        SELECT 1 from account_invoice_line ail
                        WHERE ail.account_analytic_id = line.account_analytic_id
                        AND (date %s - interval '1 month' BETWEEN ail.asset_start_date AND ail.asset_end_date)
                        )
                """, [date.strftime(DEFAULT_SERVER_DATETIME_FORMAT), date.strftime(DEFAULT_SERVER_DATETIME_FORMAT)])
            else:
                request.cr.execute("""
                    SELECT SUM(line.mrr) AS sum
                    FROM account_invoice_line AS line, account_invoice AS invoice, account_analytic_account AS analytic_account
                    WHERE (date %s BETWEEN line.asset_start_date AND line.asset_end_date) AND
                        invoice.id = line.invoice_id AND
                        invoice.type IN ('out_invoice') AND
                        invoice.state NOT IN ('draft', 'cancel') AND
                        line.account_analytic_id = analytic_account.id AND
                        analytic_account.template_id IN %s AND
                        NOT exists (
                        SELECT 1 from account_invoice_line ail
                        WHERE ail.account_analytic_id = line.account_analytic_id
                        AND (date %s - interval '1 month' BETWEEN ail.asset_start_date AND ail.asset_end_date)
                        )
                """, [date.strftime(DEFAULT_SERVER_DATETIME_FORMAT), tuple(filtered_contract_template_ids), date.strftime(DEFAULT_SERVER_DATETIME_FORMAT)])
            sql_results = request.cr.dictfetchall()
            new_mrr = 0 if not sql_results or not sql_results[0]['sum'] else sql_results[0]['sum']

            # 2. DOWN & EXPANSION
            if not filtered_contract_template_ids:
                request.cr.execute("""
                    SELECT old_line.account_analytic_id, old_line.sum AS old_sum, new_line.sum AS new_sum, (new_line.sum - old_line.sum) AS diff
                    FROM (
                        SELECT account_analytic_id, SUM(mrr) AS sum
                        FROM account_invoice_line AS line, account_invoice AS invoice
                        WHERE asset_start_date BETWEEN date %s - interval '1 months' + interval '1 days' and date %s AND
                            invoice.id = line.invoice_id AND
                            invoice.type IN ('out_invoice') AND
                            invoice.state NOT IN ('draft', 'cancel')
                        GROUP BY account_analytic_id
                        ) AS new_line,
                        (
                        SELECT account_analytic_id, SUM(mrr) AS sum
                        FROM account_invoice_line AS line, account_invoice AS invoice
                        WHERE asset_end_date BETWEEN date %s - interval '2 months' and date %s AND
                            invoice.id = line.invoice_id AND
                            invoice.type IN ('out_invoice') AND
                            invoice.state NOT IN ('draft', 'cancel')
                        GROUP BY account_analytic_id
                        ) AS old_line
                    WHERE
                        old_line.account_analytic_id = new_line.account_analytic_id
                """, [
                        date.strftime(DEFAULT_SERVER_DATETIME_FORMAT),
                        date.strftime(DEFAULT_SERVER_DATETIME_FORMAT),
                        date.strftime(DEFAULT_SERVER_DATETIME_FORMAT),
                        date.strftime(DEFAULT_SERVER_DATETIME_FORMAT)
                ])
            else:
                request.cr.execute("""
                    SELECT old_line.account_analytic_id, old_line.sum AS old_sum, new_line.sum AS new_sum, (new_line.sum - old_line.sum) AS diff
                    FROM (
                        SELECT account_analytic_id, SUM(mrr) AS sum
                        FROM account_invoice_line AS line, account_invoice AS invoice, account_analytic_account AS analytic_account
                        WHERE asset_start_date BETWEEN date %s - interval '1 months' + interval '1 days' and date %s AND
                            invoice.id = line.invoice_id AND
                            invoice.type IN ('out_invoice') AND
                            invoice.state NOT IN ('draft', 'cancel') AND
                            line.account_analytic_id = analytic_account.id AND
                            analytic_account.template_id IN %s
                        GROUP BY account_analytic_id
                        ) AS new_line,
                        (
                        SELECT account_analytic_id, SUM(mrr) AS sum
                        FROM account_invoice_line AS line, account_invoice AS invoice, account_analytic_account AS analytic_account
                        WHERE asset_end_date BETWEEN date %s - interval '2 months' and date %s AND
                            invoice.id = line.invoice_id AND
                            invoice.type IN ('out_invoice') AND
                            invoice.state NOT IN ('draft', 'cancel') AND
                            line.account_analytic_id = analytic_account.id AND
                            analytic_account.template_id IN %s
                        GROUP BY account_analytic_id
                        ) AS old_line
                    WHERE
                        old_line.account_analytic_id = new_line.account_analytic_id
                """, [
                        date.strftime(DEFAULT_SERVER_DATETIME_FORMAT),
                        date.strftime(DEFAULT_SERVER_DATETIME_FORMAT),
                        tuple(filtered_contract_template_ids),
                        date.strftime(DEFAULT_SERVER_DATETIME_FORMAT),
                        date.strftime(DEFAULT_SERVER_DATETIME_FORMAT),
                        tuple(filtered_contract_template_ids)
                ])
            sql_results = request.cr.dictfetchall()
            for account in sql_results:
                if account['diff'] > 0:
                    expansion_mrr += account['diff']
                else:
                    down_mrr -= account['diff']

            # 4. CHURNED
            if not filtered_contract_template_ids:
                request.cr.execute("""
                    SELECT SUM(line.mrr) AS sum
                    FROM account_invoice_line AS line, account_invoice AS invoice
                    WHERE (date %s - interval '1 months' BETWEEN line.asset_start_date AND line.asset_end_date) AND
                        invoice.id = line.invoice_id AND
                        invoice.type IN ('out_invoice') AND
                        invoice.state NOT IN ('draft', 'cancel') AND
                        NOT exists (
                        SELECT 1 from account_invoice_line ail
                        WHERE ail.account_analytic_id = line.account_analytic_id
                        AND (date %s BETWEEN ail.asset_start_date AND ail.asset_end_date)
                        )
                """, [date.strftime(DEFAULT_SERVER_DATETIME_FORMAT), date.strftime(DEFAULT_SERVER_DATETIME_FORMAT)])
            else:
                request.cr.execute("""
                    SELECT SUM(line.mrr) AS sum
                    FROM account_invoice_line AS line, account_invoice AS invoice, account_analytic_account AS analytic_account
                    WHERE (date %s - interval '1 months' BETWEEN line.asset_start_date AND line.asset_end_date) AND
                        invoice.id = line.invoice_id AND
                        invoice.type IN ('out_invoice') AND
                        invoice.state NOT IN ('draft', 'cancel') AND
                        line.account_analytic_id = analytic_account.id AND
                        analytic_account.template_id IN %s AND
                        NOT exists (
                        SELECT 1 from account_invoice_line ail
                        WHERE ail.account_analytic_id = line.account_analytic_id
                        AND (date %s BETWEEN ail.asset_start_date AND ail.asset_end_date)
                        )
                """, [date.strftime(DEFAULT_SERVER_DATETIME_FORMAT), tuple(filtered_contract_template_ids), date.strftime(DEFAULT_SERVER_DATETIME_FORMAT)])
            sql_results = request.cr.dictfetchall()
            cancel_mrr = 0 if not sql_results or not sql_results[0]['sum'] else sql_results[0]['sum']

            churned_mrr = cancel_mrr + down_mrr

            net_new_mrr = new_mrr + expansion_mrr - churned_mrr
            result = new_mrr, expansion_mrr, -churned_mrr, net_new_mrr

        else:
            result = 0

        return result
