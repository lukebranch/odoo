# -*- coding: utf-8 -*-

{
    'name': 'Leave Management',
    'version': '1.5',
    'author': 'Odoo SA',
    'category': 'Human Resources',
    'sequence': 27,
    'summary': 'Holidays, Allocation and Leave Requests',
    'website': 'https://www.odoo.com/page/employees',
    'description': """
Manage leaves and allocation requests
=====================================

This application controls the holiday schedule of your company. It allows employees to request holidays. Then, managers can review requests for holidays and approve or reject them. This way you can control the overall holiday planning for the company or department.

You can configure several kinds of leaves (sickness, holidays, paid days, ...) and allocate leaves to an employee or department quickly using allocation requests. An employee can also make a request for more days off by making a new Allocation. It will increase the total of available days for that leave type (if the request is accepted).

You can keep track of leaves in different ways by following reports:

* Leaves Summary
* Leaves by Department
* Leaves Analysis

A synchronization with an internal agenda (Meetings of the CRM module) is also possible in order to automatically create a meeting when a holiday request is accepted by setting up a type of meeting in Leave Type.
""",
    'depends': ['hr', 'calendar', 'resource'],
    'data': [
        'security/hr_holidays_security.xml',
        'security/ir.model.access.csv',
        'data/report_paperformat.xml',
        'data/hr_holidays_data.xml',
        'views/hr_holidays_views.xml',
        'views/inherited_hr_employee_views.xml',
        'views/inherited_hr_department_views.xml',
        'views/report_hr_holidays_summary.xml',
        'views/hr_holidays_workflow.xml',
        'views/hr_holidays_report.xml',
        'report/hr_holidays_report_view.xml',
        'report/available_holidays_view.xml',
        'wizard/hr_holidays_summary_department_view.xml',
        'wizard/hr_holidays_summary_employees_view.xml',
    ],
    'demo': ['data/hr_holidays_demo.xml'],
    'installable': True,
    'application': True
}
