# -*- coding: utf-8 -*-

from datetime import timedelta
from dateutil.relativedelta import relativedelta

from openerp import api, fields, models


class HrHolidaySummaryReport(models.AbstractModel):
    _name = 'report.hr_holidays.report_holidayssummary'

    def _get_header_info(self, start_date, holiday_type):
        start_date = fields.Date.from_string(start_date)
        return {
            'start_date': fields.Date.to_string(start_date),
            'end_date': fields.Date.to_string(start_date + relativedelta(days=59)),
            'holiday_type': 'Confirmed and Approved' if holiday_type == 'both' else holiday_type
        }

    def _get_day(self, start_date):
        res = []
        start_date = fields.Datetime.from_string(start_date)
        for x in range(0, 60):
            color = '#ababab' if start_date.strftime('%a') in ['Sat', 'Sun'] else ''
            res.append({
                'day_str': start_date.strftime('%a'),
                'day': start_date.day,
                'color': color
            })
            start_date = start_date + relativedelta(days=1)
        return res

    def _get_months(self, start_date):
        # it works for geting month name between two dates.
        res = []
        start_date = fields.Datetime.from_string(start_date)
        end_date = start_date + relativedelta(days=59)
        while start_date <= end_date:
            last_date = start_date + relativedelta(day=1, months=+1, days=-1)
            if last_date > end_date:
                last_date = end_date
            month_days = (last_date - start_date).days + 1
            res.append({'month_name': start_date.strftime('%B'), 'days': month_days})
            start_date += relativedelta(day=1, months=+1)
        return res

    def _get_leaves_summary(self, start_date, empid, holiday_type):
        res = []
        count = 0
        HrHolidays = self.env['hr.holidays']
        start_date = fields.Datetime.from_string(start_date)
        end_date = start_date + relativedelta(days=59)
        for index in range(0, 60):
            current = start_date + timedelta(index)
            res.append({'day': current.day, 'color': ''})
            if current.strftime('%a') in ['Sat', 'Sun']:
                res[index]['color'] = '#ababab'

        # count and get leave summary details.
        holiday_type = ['confirm', 'validate'] if holiday_type == 'both' else \
            ['confirm'] if holiday_type == 'Confirmed' else ['validate']
        holidays = HrHolidays.search([('employee_id', '=', empid), ('state', 'in', holiday_type),
            ('type', '=', 'remove'), ('date_from', '<=', str(end_date)),
            ('date_to', '>=', str(start_date))])
        for holiday in holidays:
            date_from = fields.Datetime.from_string(holiday.date_from)
            date_to = fields.Datetime.from_string(holiday.date_to)
            for index in range(0, ((date_to - date_from).days + 1)):
                if date_from >= start_date and date_from <= end_date:
                    res[(date_from-start_date).days]['color'] = holiday.holiday_status_id.color_name
                    count += 1
                date_from += timedelta(1)
        self.sum = count
        return res

    def _get_data_from_report(self, data):
        res = []
        HrEmployee = self.env['hr.employee']
        HrDepartment = self.env['hr.department']
        if 'depts' in data:
            for department in HrDepartment.browse(data['depts']):
                res.append({
                    'dept': department.name,
                    'data': [],
                    'color': self._get_day(data['date_from'])
                })
                employees = HrEmployee.search([('department_id', '=', department.id)])
                for emp in employees:
                    res[len(res)-1]['data'].append({
                        'emp': emp.name,
                        'display': self._get_leaves_summary(
                            data['date_from'], emp.id, data['holiday_type']),
                        'sum': self.sum
                    })
        elif 'emp' in data:
            employees = HrEmployee.browse(data['emp'])
            res.append({'data': []})
            for emp in employees:
                res[0]['data'].append({
                    'emp': emp.name,
                    'display': self._get_leaves_summary(
                        data['date_from'], emp.id, data['holiday_type']),
                    'sum': self.sum
                })
        return res

    def _get_holidays_status(self):
        res = []
        HrHolidaysStatus = self.env['hr.holidays.status']
        holidays_status = HrHolidaysStatus.search([])
        for holiday in holidays_status:
            res.append({'color': holiday.color_name, 'name': holiday.name})
        return res

    @api.multi
    def render_html(self, data=None):
        Report = self.env['report']
        holidays_report = Report._get_report_from_name('hr_holidays.report_holidayssummary')
        selected_records = self.env['hr.holidays'].browse(self.ids)
        docargs = {
            'doc_ids': self.ids,
            'doc_model': holidays_report.model,
            'docs': selected_records,
            'get_header_info': self._get_header_info(
                data['form']['date_from'], data['form']['holiday_type']),
            'get_day': self._get_day(data['form']['date_from']),
            'get_months': self._get_months(data['form']['date_from']),
            'get_data_from_report': self._get_data_from_report(data['form']),
            'get_holidays_status': self._get_holidays_status(),
        }
        return Report.render('hr_holidays.report_holidayssummary', docargs)
