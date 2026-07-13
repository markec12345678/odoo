# -*- coding: utf-8 -*-
"""Weekly timesheet container with approval workflow."""
from datetime import timedelta

from odoo import api, fields, models
from odoo.exceptions import ValidationError


def _week_start(date_value):
    """Return Monday of the week containing `date_value`."""
    return date_value - timedelta(days=date_value.weekday())


class L10nSiTimesheetWeek(models.Model):
    _name = 'l10n_si.timesheet.week'
    _description = 'Slovenian Weekly Timesheet'
    _inherit = ['mail.thread']
    _order = 'date_start DESC'

    name = fields.Char(compute='_compute_name', store=True)
    employee_id = fields.Many2one('hr.employee', required=True, tracking=True)
    date_start = fields.Date(required=True, default=lambda self: _week_start(fields.Date.today()))
    date_end = fields.Date(compute='_compute_dates', store=True)
    week_number = fields.Integer(compute='_compute_dates', store=True)
    year = fields.Integer(compute='_compute_dates', store=True)

    line_ids = fields.One2many('account.analytic.line', 'si_week_id', string='Lines')
    total_hours = fields.Float(compute='_compute_hours', store=True)

    state = fields.Selection(
        selection=[('draft', 'Osnutek'),
                   ('submitted', 'Poslano'),
                   ('approved', 'Odobreno'),
                   ('rejected', 'Zavrnjeno')],
        default='draft',
        tracking=True,
    )
    submitted_on = fields.Datetime(readonly=True, copy=False)
    submitted_to_id = fields.Many2one('res.users', readonly=True, copy=False)
    approved_on = fields.Datetime(readonly=True, copy=False)
    approved_by_id = fields.Many2one('res.users', readonly=True, copy=False)
    reject_reason = fields.Text()

    company_id = fields.Many2one(
        'res.company', string='Company',
        default=lambda self: self.env.company, required=True,
    )

    _sql_constraints = [
        ('employee_week_uniq', 'unique(employee_id, date_start, company_id)',
         'Employee can have only one timesheet per week.'),
    ]

    @api.depends('employee_id', 'date_start')
    def _compute_name(self):
        for week in self:
            week.name = f'{week.employee_id.name or ""} - {week.date_start or ""}'

    @api.depends('date_start')
    def _compute_dates(self):
        for week in self:
            if week.date_start:
                week.date_end = week.date_start + timedelta(days=6)
                iso = week.date_start.isocalendar()
                week.year = iso[0]
                week.week_number = iso[1]

    @api.depends('line_ids.unit_amount')
    def _compute_hours(self):
        for week in self:
            week.total_hours = sum(week.line_ids.mapped('unit_amount'))

    def action_submit(self):
        for week in self:
            approver = week.employee_id.si_timesheet_approver_id or week.employee_id.parent_id.user_id
            week.write({
                'state': 'submitted',
                'submitted_on': fields.Datetime.now(),
                'submitted_to_id': approver.id if approver else False,
            })
            if approver:
                week.message_post(
                    body=f'Timesheet za teden {week.date_start} čaka na odobritev.',
                    partner_ids=[approver.partner_id.id],
                )

    def action_approve(self):
        for week in self:
            week.write({
                'state': 'approved',
                'approved_on': fields.Datetime.now(),
                'approved_by_id': self.env.user.id,
            })
            # Lock the lines
            week.line_ids.write({'si_locked': True})

    def action_reject(self):
        for week in self:
            week.write({
                'state': 'rejected',
                'reject_reason': week.reject_reason or '',
            })

    def action_back_to_draft(self):
        self.write({'state': 'draft'})

    @api.model
    def _cron_remind_unsubmitted(self):
        """Monday morning: remind employees who haven't submitted last week's timesheet."""
        last_week = _week_start(fields.Date.today() - timedelta(days=7))
        Employee = self.env['hr.employee']
        existing = self.search([('date_start', '=', last_week)])
        submitted_employees = existing.mapped('employee_id')
        missing = Employee.search([
            ('id', 'not in', submitted_employees.ids),
            ('active', '=', True),
        ])
        for emp in missing:
            if emp.user_id:
                emp.message_post(
                    body=f'Prosimo oddajte timesheet za teden {last_week}.',
                    partner_ids=[emp.user_id.partner_id.id],
                )


class AccountAnalyticLine(models.Model):
    _inherit = 'account.analytic.line'

    si_week_id = fields.Many2one('l10n_si.timesheet.week', string='Timesheet Week', ondelete='set null')
    si_locked = fields.Boolean(string='Locked', default=False, copy=False)

    def write(self, vals):
        # Prevent editing locked lines
        for line in self:
            if line.si_locked and not self.env.context.get('si_unlock'):
                # Only allow if user is admin
                if not self.env.is_admin():
                    raise ValidationError(
                        f'Cannot modify locked timesheet line {line.id}.'
                    )
        return super().write(vals)
