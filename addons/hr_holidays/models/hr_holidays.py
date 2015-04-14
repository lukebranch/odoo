# -*- coding: utf-8 -*-

import logging
import math
from datetime import timedelta

from openerp import api, fields, models, _
from openerp.exceptions import AccessError, UserError

_logger = logging.getLogger(__name__)


class HrHolidaysStatus(models.Model):
    _name = "hr.holidays.status"
    _description = "Leave Type"

    @api.multi
    def name_get(self):
        if not self.env.context.get('employee_id'):
            """ leave counts is based on employee_id, would be inaccurate if
                not based on correct employee """
            return super(HrHolidaysStatus, self).name_get()
        result = []
        for record in self:
            name = record.name
            if not record.limit:
                name = name + ('  (%g/%g)' %
                    (record.virtual_remaining_leaves or 0.0, record.max_leaves or 0.0))
            result.append((record.id, name))
        return result

    name = fields.Char(string='Leave Type', size=64, required=True, translate=True)
    categ_id = fields.Many2one(comodel_name='calendar.event.type', string='Meeting Type',
        help='Once a leave is validated, Odoo will create a corresponding '
             'meeting of this type in the calendar.')
    color_name = fields.Selection([
        ('red', 'Red'),
        ('blue', 'Blue'),
        ('lightgreen', 'Light Green'),
        ('lightblue', 'Light Blue'),
        ('lightyellow', 'Light Yellow'),
        ('magenta', 'Magenta'),
        ('lightcyan', 'Light Cyan'),
        ('black', 'Black'),
        ('lightpink', 'Light Pink'),
        ('brown', 'Brown'),
        ('violet', 'Violet'),
        ('lightcoral', 'Light Coral'),
        ('lightsalmon', 'Light Salmon'),
        ('lavender', 'Lavender'),
        ('wheat', 'Wheat'),
        ('ivory', 'Ivory')
    ], string='Color in Report', default='red', required=True,
        help='This color will be used in the leaves summary '
             'located in Reporting\Leaves by Department.')
    limit = fields.Boolean(string='Allow to Override Limit',
        help='If you select this check box, the system allows the employees '
             'to take more leaves than the available ones for this type and '
             'will not take them into account for the "Remaining Legal '
             'Leaves" defined on the employee form.')
    active = fields.Boolean(string='Active', default=True,
        help='If the active field is set to false, it will allow you to hide '
             'the leave type without removing it.')
    max_leaves = fields.Integer(compute='_compute_user_left_days', string='Maximum Allowed',
        help='This value is given by the sum of all holidays requests with a '
             'positive value.')
    leaves_taken = fields.Integer(compute='_compute_user_left_days', string='Leaves Already Taken',
        help='This value is given by the sum of all holidays requests with a negative value.')
    remaining_leaves = fields.Integer(compute='_compute_user_left_days', string='Remaining Leaves',
        help='Maximum Leaves Allowed - Leaves Already Taken')
    virtual_remaining_leaves = fields.Integer(compute='_compute_user_left_days',
        string='Virtual Remaining Leaves',
        help='Maximum Leaves Allowed - Leaves Already Taken - Leaves Waiting Approval')
    double_validation = fields.Boolean('Apply Double Validation',
        help='When selected, the Allocation/Leave Requests for this type '
             'require a second validation to be approved.')

    @api.one
    def _compute_user_left_days(self):
        if self.env.context.get('employee_id'):
            employee_id = self.env.context['employee_id']
        else:
            employee = self.env['hr.employee'].search([
                ('user_id', '=', self.env.user.id)], limit=1)
            employee_id = employee.id or False
        if employee_id:
            self.get_days(employee_id)

    @api.model
    def _search(self, args, offset=0, limit=None, order=None, count=False, access_rights_uid=None):
        """ Override _search to order the results, according to some employee.
        The order is the following

         - limit (limited leaves first, such as Legal Leaves)
         - virtual remaining leaves (higher the better, so using reverse on sorted)

        This override is necessary because those fields are not stored and
        depends on an employee_id given in context. This sort will be done
        when there is an employee_id in context and that no other order has
        been given to the method. """
        status_ids = super(HrHolidaysStatus, self)._search(args, offset=offset,
            limit=limit, order=order, count=count, access_rights_uid=access_rights_uid)

        if not count and not order and self.env.context.get('employee_id'):
            leaves = self.browse(status_ids)
            sort_key = lambda l: (not l.limit, l.virtual_remaining_leaves)
            return map(int, leaves.sorted(key=sort_key, reverse=True))
        return status_ids

    def get_days(self, employee_id):
        holidays = self.env['hr.holidays'].search([
            ('employee_id', '=', employee_id),
            ('state', 'in', ['confirm', 'validate1', 'validate']),
            ('holiday_status_id', '=', self.id)
        ])
        for holiday in holidays:
            if holiday.holiday_status_id.id == self.id:
                if holiday.type == 'add':
                    if holiday.state == 'validate':
                        # note: add only validated allocation even for the virtual
                        # count; otherwise pending then refused allocation allow
                        # the employee to create more leaves than possible
                        self.virtual_remaining_leaves += holiday.number_of_days_temp
                        self.max_leaves += holiday.number_of_days_temp
                        self.remaining_leaves += holiday.number_of_days_temp
                elif holiday.type == 'remove':  # number of days is negative
                    self.virtual_remaining_leaves -= holiday.number_of_days_temp
                    if holiday.state == 'validate':
                        self.leaves_taken += holiday.number_of_days_temp
                        self.remaining_leaves -= holiday.number_of_days_temp

    def sufficient_leaves_available(self, employee_id, status_id):
        result = {}
        result[status_id] = dict(max_leaves=0, leaves_taken=0, remaining_leaves=0,
            virtual_remaining_leaves=0)
        holidays = self.env['hr.holidays'].search([('employee_id', '=', employee_id),
            ('state', 'in', ['confirm', 'validate1', 'validate']),
            ('holiday_status_id', '=', status_id)])
        for holiday in holidays:
            if holiday.holiday_status_id.id == status_id:
                status_dict = result[status_id]
                if holiday.type == 'add':
                    if holiday.state == 'validate':
                        status_dict['virtual_remaining_leaves'] += holiday.number_of_days_temp
                        status_dict['max_leaves'] += holiday.number_of_days_temp
                        status_dict['remaining_leaves'] += holiday.number_of_days_temp
                elif holiday.type == 'remove':
                    status_dict['virtual_remaining_leaves'] -= holiday.number_of_days_temp
                    if holiday.state == 'validate':
                        status_dict['leaves_taken'] += holiday.number_of_days_temp
                        status_dict['remaining_leaves'] -= holiday.number_of_days_temp
        return result


class HrHolidays(models.Model):
    _name = "hr.holidays"
    _description = "Leave"
    _order = "type desc, date_from asc"
    _inherit = ['mail.thread', 'ir.needaction_mixin']

    name = fields.Char(string='Description', size=64)
    state = fields.Selection([
        ('draft', 'To Submit'),
        ('cancel', 'Cancelled'),
        ('confirm', 'To Approve'),
        ('refuse', 'Refused'),
        ('validate1', 'Second Approval'),
        ('validate', 'Approved')
    ], string='Status', readonly=True, track_visibility='onchange', copy=False,
        help='The status is set to \'To Submit\', when a holiday request is created.\n'
             'The status is \'To Approve\', when holiday request is confirmed by user.\n'
             'The status is \'Refused\', when holiday request is refused by manager.\n'
             'The status is \'Approved\', when holiday request is approved by manager.',
        default='confirm')
    payslip_status = fields.Boolean(string='Reported in last payslips',
        help='Green this button when the leave has been taken into account '
             'in the payslip.', default=False)
    report_note = fields.Text(string='HR Comments')
    user_id = fields.Many2one(comodel_name='res.users', related='employee_id.user_id',
        string='User', default=lambda self: self.env.user.id)
    date_from = fields.Datetime(string='Start Date', readonly=True,
        states={'draft': [('readonly', False)], 'confirm': [('readonly', False)]},
        index=True, copy=False)
    date_to = fields.Datetime(string='End Date', readonly=True,
        states={'draft': [('readonly', False)], 'confirm': [('readonly', False)]},
        copy=False)
    holiday_status_id = fields.Many2one('hr.holidays.status',
        string='Leave Type', required=True, readonly=True,
        states={'draft': [('readonly', False)], 'confirm': [('readonly', False)]})
    employee_id = fields.Many2one('hr.employee', string='Employee', index=True,
        invisible=False, readonly=True, default=lambda self: self._default_employee_get(),
        states={'draft': [('readonly', False)], 'confirm': [('readonly', False)]})
    manager_id = fields.Many2one('hr.employee', string='First Approval',
        invisible=False, readonly=True, copy=False,
        help='This area is automatically filled by the user who validate the leave')
    notes = fields.Text(string='Reasons', readonly=True,
        states={'draft': [('readonly', False)], 'confirm': [('readonly', False)]})
    number_of_days_temp = fields.Float(string='Allocation', readonly=True,
        states={'draft': [('readonly', False)], 'confirm': [('readonly', False)]},
        copy=False)
    number_of_days = fields.Float(compute='_compute_number_of_days',
        string='Number of Days', store=True)
    meeting_id = fields.Many2one('calendar.event', string='Meeting')
    type = fields.Selection([
        ('remove', 'Leave Request'),
        ('add', 'Allocation Request')
    ], string='Request Type', required=True, readonly=True, index=True,
        states={'draft': [('readonly', False)], 'confirm': [('readonly', False)]},
        help='Choose \'Leave Request\' if someone wants to take an off-day. \n'
             'Choose \'Allocation Request\' if you want to increase the number '
             'of leaves available for someone', default='remove')
    parent_id = fields.Many2one('hr.holidays', string='Parent')
    linked_request_ids = fields.One2many('hr.holidays', 'parent_id',
        string='Linked Requests')
    department_id = fields.Many2one(comodel_name='hr.department',
        related='employee_id.department_id', string='Department', readonly=True, store=True)
    category_id = fields.Many2one('hr.employee.category', string='Employee Tag',
        help='Category of Employee', readonly=True,
        states={'draft': [('readonly', False)], 'confirm': [('readonly', False)]})
    holiday_type = fields.Selection([
        ('employee', 'By Employee'),
        ('category', 'By Employee Tag')], string='Allocation Mode',
        readonly=True, required=True,
        states={'draft': [('readonly', False)], 'confirm': [('readonly', False)]},
        help='By Employee: Allocation/Request for individual Employee,'
             'By Employee Tag: Allocation/Request for group of employees in category',
        default='employee')
    second_manager_id = fields.Many2one('hr.employee', string='Second Approval',
        readonly=True, copy=False,
        help='This area is automaticly filled by the user who validate the '
             'leave with second level (If Leave type need second validation)')
    double_validation = fields.Boolean(comodel_name='hr.holidays.status',
        related='holiday_status_id.double_validation', string='Apply Double Validation')
    can_reset = fields.Boolean(compute='_compute_get_can_reset', string="Can reset")

    _sql_constraints = [
        ('type_value', "CHECK ( \
                (holiday_type='employee' AND employee_id IS NOT NULL) or \
                (holiday_type='category' AND category_id IS NOT NULL) \
            )", _("The employee or employee category of this request is missing."
                  "Please make sure that your user login is linked to an employee.")),
        ('date_check2', "CHECK ( \
                (type='add') OR (date_from <= date_to) \
            )", _("The start date must be anterior to the end date.")),
        ('date_check', "CHECK ( number_of_days_temp >= 0 )",
            _("The number of days must be greater than 0.")),
    ]

    def _default_employee_get(self):
        if self.env.context.get('default_employee_id'):
            return self.env.context['default_employee_id']
        employee = self.env['hr.employee'].search([('user_id', '=', self.env.user.id)], limit=1)
        return employee.id or False

    @api.depends('type')
    def _compute_number_of_days(self):
        if self.type == 'remove':
            self.number_of_days = -self.number_of_days_temp
        else:
            self.number_of_days = self.number_of_days_temp

    def _compute_get_can_reset(self):
        """User can reset a leave request if it is its own leave request or if
        he is an Hr Manager. """
        group_hr_manager_id = self.env.ref('base.group_hr_manager').id
        user_groups = [g.id for g in self.env.user.groups_id]
        for record in self:
            if group_hr_manager_id in user_groups:
                record.can_reset = True
            if record.employee_id.user_id.id == self.env.user.id:
                record.can_reset = True

    @api.multi
    def _track_subtype(self, init_values):
        if 'state' in init_values and self.state == 'validate':
            return 'hr_holidays.mt_holidays_approved'
        elif 'state' in init_values and self.state == 'validate1':
            return 'hr_holidays.mt_holidays_first_validated'
        elif 'state' in init_values and self.state == 'confirm':
            return 'hr_holidays.mt_holidays_confirmed'
        elif 'state' in init_values and self.state == 'refuse':
            return 'hr_holidays.mt_holidays_refused'
        return super(HrHolidays, self)._track_subtype(init_values)

    @api.constrains('date_from', 'date_to')
    def _check_date(self):
        domain = [
            ('date_from', '<=', self.date_to),
            ('date_to', '>=', self.date_from),
            ('employee_id', '=', self.employee_id.id),
            ('id', '!=', self.id),
            ('state', 'not in', ['cancel', 'refuse']),
        ]
        leaves_taken = self.search_count(domain)
        if leaves_taken:
            raise UserError(_('You can not have 2 leaves that overlaps on same day!'))

    @api.constrains('state', 'number_of_days_temp')
    def _check_holidays(self):
        if self.holiday_type != 'employee' or self.type != 'remove' or \
           not self.employee_id or self.holiday_status_id.limit:
            return False

        leave_days = self.env['hr.holidays.status'].sufficient_leaves_available(
            self.employee_id.id, self.holiday_status_id.id)[self.holiday_status_id.id]
        if leave_days['remaining_leaves'] < 0 or \
           leave_days['virtual_remaining_leaves'] < 0:
            raise UserError(_('The number of remaining leaves is not sufficient for this leave '
                              'type.\n Please verify also the leaves waiting for validation.'))

    @api.onchange('holiday_type', 'employee_id')
    def _onchange_type(self):
        employee = self.env['hr.employee'].search([('user_id', '=', self.env.user.id)], limit=1)
        if self.holiday_type == 'employee' and not self.employee_id:
            self.employee_id = employee.id
        elif self.holiday_type != 'employee':
            self.employee_id = False

    @api.onchange('employee_id')
    def _onchange_employee(self):
        self.department_id = self.employee_id.department_id.id

    @api.onchange('date_from', 'date_to')
    def _onchange_date_from(self):
        """If there are no date set for date_to, automatically set one 8 hours
        later than the date_from. Also update the number_of_days."""
        # date_to has to be greater than date_from
        if (self.date_from and self.date_to) and (self.date_from > self.date_to):
            raise UserError(_('The start date must be anterior to the end date.'))

        # No date_to set so far: automatically compute one 8 hours later
        if self.date_from and not self.date_to:
            date_from = fields.Datetime.from_string(self.date_from)
            date_to_with_delta = date_from + timedelta(hours=8)
            self.date_to = fields.Datetime.to_string(date_to_with_delta)

        # Compute and update the number of days
        if (self.date_to and self.date_from) and (self.date_from <= self.date_to):
            diff_day = self._get_number_of_days(self.date_from, self.date_to)
            self.number_of_days_temp = round(math.floor(diff_day)) + 1
        else:
            self.number_of_days_temp = 0

    @api.onchange('date_from', 'date_to')
    def _onchange_date_to(self):
        """Update the number_of_days."""
        # date_to has to be greater than date_from
        if (self.date_from and self.date_to) and (self.date_from > self.date_to):
            raise UserError(_('The start date must be anterior to the end date.'))

        # Compute and update the number of days
        if (self.date_to and self.date_from) and (self.date_from <= self.date_to):
            diff_day = self._get_number_of_days(self.date_from, self.date_to)
            self.number_of_days_temp = round(math.floor(diff_day)) + 1
        else:
            self.number_of_days_temp = 0

    @api.one
    def toggle_payslip_status(self):
        if self.payslip_status:
            return self.write({'payslip_status': False})
        else:
            return self.write({'payslip_status': True})

    @api.model
    def create(self, vals):
        """Override to avoid automatic logging of creation"""
        ctx = dict(self.env.context, mail_create_nolog=True)
        if vals.get('state') and \
           vals['state'] not in ['draft', 'confirm', 'cancel'] and \
           not self.env['res.users'].has_group('base.group_hr_user'):
            raise AccessError(_('You cannot set a leave request as \'%s\'. '
                                'Contact a human resource manager.') % vals['state'])
        holiday = super(HrHolidays, self.with_context(ctx)).create(vals)
        holiday.with_context(ctx).add_follower(vals.get('employee_id'))
        return holiday

    @api.multi
    def write(self, vals):
        if vals.get('state') and \
           vals['state'] not in ['draft', 'confirm', 'cancel'] and \
           not self.env['res.users'].has_group('base.group_hr_user'):
            raise AccessError(_('You cannot set a leave request as \'%s\'. '
                                'Contact a human resource manager.') % vals.get('state'))
        hr_holiday_id = super(HrHolidays, self).write(vals)
        self.add_follower(vals.get('employee_id'))
        return hr_holiday_id

    @api.multi
    def unlink(self):
        for record in self:
            record.ensure_one()
            if record.state not in ['draft', 'cancel', 'confirm']:
                raise UserError(_('You cannot delete a leave which is '
                                  'in %s state.') % (record.state))
        return super(HrHolidays, self).unlink()

    def _get_number_of_days(self, date_from, date_to):
        """Returns a float equals to the timedelta between two dates
        given as string."""
        from_dt = fields.Datetime.from_string(date_from)
        to_dt = fields.Datetime.from_string(date_to)
        diff = to_dt - from_dt
        diff_day = diff.days + float(diff.seconds) / 86400
        return diff_day

    def add_follower(self, employee_id):
        employee = self.env['hr.employee'].browse(employee_id)
        if employee and employee.user_id:
            self.message_subscribe_users(user_ids=[employee.user_id.id])

    def _create_resource_leave(self):
        """This method will create entry in resource calendar leave object
        at the time of holidays validated """
        vals = {
            'name': self.name,
            'date_from': self.date_from,
            'holiday_id': self.id,
            'date_to': self.date_to,
            'resource_id': self.employee_id.resource_id.id,
            'calendar_id': self.employee_id.resource_id.calendar_id.id
        }
        self.env['resource.calendar.leaves'].create(vals)

    def _remove_resource_leave(self):
        """This method will create entry in resource calendar leave object
        at the time of holidays cancel/removed"""
        ResourceCalendarLeaves = self.env['resource.calendar.leaves'].search(
            [('holiday_id', '=', self.id)])
        ResourceCalendarLeaves.unlink()

    def holidays_reset(self):
        self.write({
            'state': 'draft',
            'manager_id': False,
            'second_manager_id': False,
        })
        unlink_request = self.env['hr.holidays']
        for record in self.linked_request_ids:
            record.holidays_reset()
            unlink_request += record
        unlink_request.unlink()
        return True

    def holidays_first_validate(self):
        employee = self.env['hr.employee'].search([('user_id', '=', self.env.user.id)], limit=1)
        self.write({
            'state': 'validate1',
            'manager_id': employee.id
        })

    def holidays_validate(self):
        HrEmployee = self.env['hr.employee']
        CalendarEvent = self.env['calendar.event']
        employee = HrEmployee.search([('user_id', '=', self.env.user.id)], limit=1)
        self.state = 'validate'
        if self.double_validation:
            self.second_manager_id = employee.id
        else:
            self.manager_id = employee.id

        if self.holiday_type == 'employee' and self.type == 'remove':
            meeting_vals = {
                'name': self.name or _('Leave Request'),
                'categ_ids': (self.holiday_status_id.categ_id and
                              [(6, 0, [self.holiday_status_id.categ_id.id])] or []),
                'duration': self.number_of_days_temp * 8,
                'description': self.notes,
                'user_id': self.user_id.id,
                'start': self.date_from,
                'stop': self.date_to,
                'allday': False,
                'state': 'open',   # to block that meeting date in the calendar
                'class': 'confidential'
            }
            #Add the partner_id (if exist) as an attendee
            if self.user_id and self.user_id.partner_id:
                meeting_vals['partner_ids'] = [(4, self.user_id.partner_id.id)]

            meeting_id = CalendarEvent.with_context(no_email=True).create(meeting_vals)
            self._create_resource_leave()
            self.write({'meeting_id': meeting_id.id})
        elif self.holiday_type == 'category':
            employees = HrEmployee.search([
                ('category_ids', 'child_of', [self.category_id.id])
            ])
            leaves = []
            for employee in employees:
                vals = {
                    'name': self.name,
                    'type': self.type,
                    'holiday_type': 'employee',
                    'holiday_status_id': self.holiday_status_id.id,
                    'date_from': self.date_from,
                    'date_to': self.date_to,
                    'notes': self.notes,
                    'number_of_days_temp': self.number_of_days_temp,
                    'parent_id': self.id,
                    'employee_id': employee.id
                }
                leaves.append(self.create(vals))
            for leave in leaves:
                # TODO is it necessary to interleave the calls?
                for sig in ('confirm', 'validate', 'second_validate'):
                    leave.signal_workflow(sig)

    def holidays_confirm(self):
        if self.employee_id.parent_id.user_id:
            self.message_subscribe_users([self.employee_id.parent_id.user_id.id])
        return self.write({'state': 'confirm'})

    def holidays_refuse(self):
        HrEmployee = self.env['hr.employee']
        employee = HrEmployee.search([('user_id', '=', self.env.user.id)], limit=1)
        for record in self:
            if self.state == 'validate1':
                self.write({'state': 'refuse', 'manager_id': employee.id})
            else:
                self.write({'state': 'refuse', 'second_manager_id': employee.id})
        self.holidays_cancel()

    def holidays_cancel(self):
        if self.meeting_id:
            self.meeting_id.unlink()

        self.signal_workflow('refuse')
        self._remove_resource_leave()


class ResourceCalendarLeaves(models.Model):
    _description = "Leave Detail"
    _inherit = "resource.calendar.leaves"

    holiday_id = fields.Many2one("hr.holidays", "Leave Request")
