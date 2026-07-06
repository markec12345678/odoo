# -*- coding: utf-8 -*-
"""Roster assignment - določena oseba na določeno izmeno na določen dan."""
from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class L10nSiRosterAssignment(models.Model):
    _name = 'l10n_si.roster.assignment'
    _description = 'Slovenian Roster Assignment'
    _inherit = ['mail.thread']
    _order = 'date, shift_id'

    name = fields.Char(compute='_compute_name', store=True)
    number = fields.Char(copy=False, readonly=True, default='/')
    company_id = fields.Many2one(
        'res.company', string='Company',
        default=lambda self: self.env.company, required=True,
    )

    # Kdo, kdaj, kaj
    employee_id = fields.Many2one('hr.employee', required=True, tracking=True, ondelete='restrict')
    shift_id = fields.Many2one('l10n_si.roster.shift', required=True, ondelete='restrict')
    date = fields.Date(required=True, default=fields.Date.today)

    # Čas
    scheduled_start = fields.Datetime(compute='_compute_scheduled', store=True)
    scheduled_end = fields.Datetime(compute='_compute_scheduled', store=True)
    scheduled_hours = fields.Float(related='shift_id.duration_hours', store=True)

    actual_start = fields.Datetime(readonly=True, copy=False)
    actual_end = fields.Datetime(readonly=True, copy=False)
    actual_hours = fields.Float(compute='_compute_actual', store=True)

    # Odmori
    break_minutes = fields.Integer(default=30, string='Odmor (min)')

    # Status
    state = fields.Selection(
        selection=[('draft', 'Osnutek'),
                   ('confirmed', 'Potrjeno'),
                   ('in_progress', 'V izvedbi'),
                   ('completed', 'Opravljeno'),
                   ('no_show', 'Ni prišel'),
                   ('cancelled', 'Preklicano')],
        default='draft',
        tracking=True,
    )

    # Nadure
    is_overtime = fields.Boolean(default=False, string='Nadure',
                                   help='Ročno označene nadure.')
    overtime_hours = fields.Float(compute='_compute_overtime', store=True)

    # Spremenljivica
    swap_request_id = fields.Many2one('l10n_si.roster.swap.request', string='Zahteva za zamenjavo')

    # Povezana prisotnost
    attendance_id = fields.Many2one('hr.attendance', string='Prisotnost')

    notes = fields.Text()

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('number', '/') == '/':
                vals['number'] = self.env['ir.sequence'].next_by_code('l10n_si.roster.assignment') or '/'
        return super().create(vals_list)

    @api.depends('employee_id', 'shift_id', 'date')
    def _compute_name(self):
        for a in self:
            emp = a.employee_id.name or ''
            shift = a.shift_id.name or ''
            date = a.date.strftime('%d.%m.%Y') if a.date else ''
            a.name = f'{emp} - {shift} - {date}'

    @api.depends('date', 'shift_id')
    def _compute_scheduled(self):
        from datetime import datetime, time
        for a in self:
            if a.date and a.shift_id:
                # Start
                start_h = int(a.shift_id.start_hour)
                start_m = int((a.shift_id.start_hour - start_h) * 60)
                a.scheduled_start = datetime.combine(a.date, time(start_h, start_m))
                # End (could be next day if night shift)
                end_h_int = int(a.shift_id.end_hour)
                end_m = int((a.shift_id.end_hour - end_h_int) * 60)
                from datetime import timedelta
                end_date = a.date
                if a.shift_id.end_hour <= a.shift_id.start_hour:
                    end_date = a.date + timedelta(days=1)
                a.scheduled_end = datetime.combine(end_date, time(end_h_int, end_m))
            else:
                a.scheduled_start = False
                a.scheduled_end = False

    @api.depends('actual_start', 'actual_end')
    def _compute_actual(self):
        for a in self:
            if a.actual_start and a.actual_end:
                delta = a.actual_end - a.actual_start
                a.actual_hours = delta.total_seconds() / 3600.0
            else:
                a.actual_hours = 0.0

    @api.depends('actual_hours', 'scheduled_hours', 'is_overtime')
    def _compute_overtime(self):
        for a in self:
            if a.actual_hours > a.scheduled_hours:
                a.overtime_hours = a.actual_hours - a.scheduled_hours
            elif a.is_overtime:
                a.overtime_hours = a.actual_hours
            else:
                a.overtime_hours = 0.0

    @api.constrains('employee_id', 'date', 'shift_id')
    def _check_overlap(self):
        """Prepreči prekrivanje izmen za isto osebo."""
        for a in self:
            if not a.scheduled_start or not a.scheduled_end:
                continue
            overlapping = self.search([
                ('employee_id', '=', a.employee_id.id),
                ('date', '=', a.date),
                ('id', '!=', a.id),
                ('state', 'in', ['draft', 'confirmed', 'in_progress']),
            ])
            for other in overlapping:
                if not other.scheduled_start or not other.scheduled_end:
                    continue
                if (a.scheduled_start < other.scheduled_end and
                        a.scheduled_end > other.scheduled_start):
                    raise ValidationError(_(
                        'Prekrivanje izmen za %(emp)s na %(date)s (%(shift1)s in %(shift2)s)',
                        emp=a.employee_id.name, date=a.date,
                        shift1=a.shift_id.name, shift2=other.shift_id.name,
                    ))

    @api.constrains('employee_id', 'date')
    def _check_min_rest(self):
        """ZDR-1: minimalno 11 ur počitka med izmenama."""
        from datetime import timedelta
        for a in self:
            if not a.scheduled_end:
                continue
            # Find previous assignment
            prev = self.search([
                ('employee_id', '=', a.employee_id.id),
                ('date', '<', a.date),
                ('state', 'in', ['confirmed', 'completed']),
            ], order='date DESC', limit=1)
            if prev and prev.scheduled_end:
                rest = a.scheduled_start - prev.scheduled_end
                if rest < timedelta(hours=11):
                    raise ValidationError(_(
                        'Premalo počitka (%(h).1fh) za %(emp)s med izmenama na %(d1)s in %(d2)s. ZDR-1 zahteva min. 11 ur.',
                        h=rest.total_seconds() / 3600, emp=a.employee_id.name,
                        d1=prev.date, d2=a.date,
                    ))

    def action_confirm(self):
        self.write({'state': 'confirmed'})

    def action_start(self):
        for a in self:
            a.write({
                'state': 'in_progress',
                'actual_start': fields.Datetime.now(),
            })

    def action_complete(self):
        for a in self:
            a.write({
                'state': 'completed',
                'actual_end': fields.Datetime.now(),
            })

    def action_no_show(self):
        self.write({'state': 'no_show'})

    def action_cancel(self):
        self.write({'state': 'cancelled'})


class L10nSiRosterSwapRequest(models.Model):
    _name = 'l10n_si.roster.swap.request'
    _description = 'Slovenian Roster Swap Request'
    _inherit = ['mail.thread']
    _order = 'create_date DESC'

    name = fields.Char(copy=False, readonly=True, default='/')
    requesting_employee_id = fields.Many2one('hr.employee', required=True, string='Prosi za zamenjavo')
    target_employee_id = fields.Many2one('hr.employee', required=True, string='Zamenja z')
    assignment_id = fields.Many2one('l10n_si.roster.assignment', required=True, ondelete='cascade')

    reason = fields.Text(required=True)
    state = fields.Selection(
        selection=[('requested', 'Prošnja poslana'),
                   ('accepted', 'Sprejeto'),
                   ('rejected', 'Zavrnjeno'),
                   ('cancelled', 'Preklicano')],
        default='requested',
        tracking=True,
    )
    accepted_on = fields.Datetime(readonly=True, copy=False)
    notes = fields.Text()

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', '/') == '/':
                vals['name'] = self.env['ir.sequence'].next_by_code('l10n_si.roster.swap.request') or '/'
        return super().create(vals_list)

    def action_accept(self):
        for req in self:
            # Reassign the assignment to target employee
            req.assignment_id.write({'employee_id': req.target_employee_id.id})
            req.write({
                'state': 'accepted',
                'accepted_on': fields.Datetime.now(),
            })

    def action_reject(self):
        self.write({'state': 'rejected'})

    def action_cancel(self):
        self.write({'state': 'cancelled'})
