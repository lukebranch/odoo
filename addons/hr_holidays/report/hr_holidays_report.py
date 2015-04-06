# -*- coding: utf-8 -*-

from openerp import tools
from openerp import models, fields


class HrHolidaysRemainingLeavesUser(models.Model):
    _name = "hr.holidays.remaining.leaves.user"
    _description = "Total holidays by type"
    _auto = False

    name = fields.Char(string='Employee')
    no_of_leaves = fields.Integer(string='Remaining leaves')
    user_id = fields.Many2one(comodel_name='res.users', string='User')
    leave_type = fields.Char(string='Leave Type')

    def init(seld, cr):
        tools.drop_view_if_exists(cr, 'hr_holidays_remaining_leaves_user')
        cr.execute("""
            CREATE or REPLACE view hr_holidays_remaining_leaves_user as (
                 SELECT
                    min(hrs.id) as id,
                    rr.name as name,
                    sum(hrs.number_of_days) as no_of_leaves,
                    rr.user_id as user_id,
                    hhs.name as leave_type
                FROM
                    hr_holidays as hrs, hr_employee as hre,
                    resource_resource as rr,hr_holidays_status as hhs
                WHERE
                    hrs.employee_id = hre.id and
                    hre.resource_id =  rr.id and
                    hhs.id = hrs.holiday_status_id
                GROUP BY
                    rr.name,rr.user_id,hhs.name
            )
        """)
