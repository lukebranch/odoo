# -*- coding: utf-8 -*-

import time

from openerp import api, fields, models


class HrHolidaysSummaryEmployee(models.TransientModel):
    _name = 'hr.holidays.summary.employee'
    _description = 'HR Leaves Summary Report By Employee'

    date_from = fields.Date(string='From', required=True,
        default=lambda self: time.strftime('%Y-%m-01'))
    emp = fields.Many2many('hr.employee', 'summary_emp_rel', 'sum_id', 'emp_id',
        string='Employee(s)')
    holiday_type = fields.Selection([
        ('Approved', 'Approved'),
        ('Confirmed', 'Confirmed'),
        ('both', 'Both Approved and Confirmed')
    ], string='Select Leave Type', required=True, default='Approved')

    @api.multi
    def print_report(self):
        record = self.read()[0]
        record['emp'] = self.env.context.get('active_ids', [])
        datas = {
            'ids': [],
            'model': 'hr.employee',
            'form': record
        }
        return self.env['report'].get_action(self,
            'hr_holidays.report_holidayssummary', data=datas)
