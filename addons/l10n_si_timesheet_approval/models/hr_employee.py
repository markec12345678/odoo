# -*- coding: utf-8 -*-
from odoo import fields, models


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    si_timesheet_approver_id = fields.Many2one(
        'res.users', string='Approver for timesheets',
        help='If empty, the direct manager is used.',
    )
