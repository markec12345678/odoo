# -*- coding: utf-8 -*-
from odoo import fields, models


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    si_default_shift_id = fields.Many2one('l10n_si.roster.shift', string='Privzeta izmena')
    si_can_work_night = fields.Boolean(string='Lahko dela nočne', default=True)
    si_can_work_weekend = fields.Boolean(string='Lahko dela vikende', default=True)
    si_preferred_days_off = fields.Char(string='Željeni prosti dnevi',
                                          help='npr. "nedelja, torek"')
    si_weekly_hours_target = fields.Float(default=40.0, string='Ciljne ure/teden')
    si_weekly_hours_max = fields.Float(default=48.0, string='Max ure/teden (ZDR-1)')

    si_assignments_this_week = fields.Integer(compute='_compute_week_stats', store=False)
    si_hours_this_week = fields.Float(compute='_compute_week_stats', store=False)

    def _compute_week_stats(self):
        from datetime import date, timedelta
        today = date.today()
        monday = today - timedelta(days=today.weekday())
        sunday = monday + timedelta(days=6)
        for emp in self:
            assignments = self.env['l10n_si.roster.assignment'].search([
                ('employee_id', '=', emp.id),
                ('date', '>=', monday),
                ('date', '<=', sunday),
                ('state', 'in', ['confirmed', 'completed']),
            ])
            emp.si_assignments_this_week = len(assignments)
            emp.si_hours_this_week = sum(a.actual_hours or a.scheduled_hours for a in assignments)
