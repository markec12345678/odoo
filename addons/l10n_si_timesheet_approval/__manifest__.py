# -*- coding: utf-8 -*-
{
    'name': 'Slovenian Timesheet Approval',
    'summary': 'Weekly timesheet approval workflow with manager review',
    'version': '19.0.1.0.0',
    'category': 'Human Resources/Timesheets',
    'description': """
Slovenian Timesheet Approval
=============================

Adds weekly approval workflow to standard `hr_timesheet`:
* Employee submits timesheet for week
* Manager reviews + approves/rejects
* Locked timesheets cannot be edited
* Auto-reminder for unsubmitted timesheets
* Integration with payroll (l10n_si_hr_payroll_community)

Replaces Enterprise `hr_timesheet_approval`.
""",
    'author': 'markec12345678',
    'website': 'https://github.com/markec12345678/odoo',
    'license': 'LGPL-3',
    'depends': ['hr_timesheet'],
    'data': [
        'security/ir.model.access.csv',
        'data/ir_cron_data.xml',
        'views/l10n_si_timesheet_week_views.xml',
        'views/hr_employee_views.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
