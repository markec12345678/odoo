# -*- coding: utf-8 -*-
"""Preventive maintenance schedule — generates maintenance requests on a recurring basis."""
from datetime import timedelta

from odoo import api, fields, models


class L10nSiMaintenanceSchedule(models.Model):
    _name = 'l10n_si.maintenance.schedule'
    _description = 'Slovenian Preventive Maintenance Schedule'
    _inherit = ['mail.thread']
    _order = 'next_run_date'

    name = fields.Char(required=True, tracking=True)
    equipment_id = fields.Many2one('maintenance.equipment', required=True, ondelete='cascade')
    active = fields.Boolean(default=True)
    company_id = fields.Many2one(
        'res.company', related='equipment_id.company_id', store=True,
    )

    # Schedule
    frequency = fields.Selection(
        selection=[('daily', 'Dnevno'),
                   ('weekly', 'Tedensko'),
                   ('monthly', 'Mesečno'),
                   ('quarterly', 'Kvartalno'),
                   ('yearly', 'Letno')],
        required=True,
        default='monthly',
    )
    frequency_interval = fields.Integer(
        default=1, required=True,
        help='E.g. every 2 weeks = frequency=weekly, interval=2.',
    )

    # Description of work
    description = fields.Html(required=True)
    estimated_duration_hours = fields.Float(default=1.0)
    technician_id = fields.Many2one('hr.employee', string='Assigned technician')

    # State
    next_run_date = fields.Date(required=True, default=fields.Date.today)
    last_run_date = fields.Date(readonly=True, copy=False)
    request_ids = fields.One2many('maintenance.request', 'si_schedule_id', string='Generated Requests')

    def _generate_request(self):
        """Create a maintenance.request from this schedule."""
        self.ensure_one()
        Stage = self.env['maintenance.stage']
        first_stage = Stage.search([], limit=1) or Stage.create({'name': 'New'})
        req = self.env['maintenance.request'].create({
            'name': f'[Preventivno] {self.name} - {self.equipment_id.name}',
            'equipment_id': self.equipment_id.id,
            'description': self.description,
            'user_id': self.technician_id.user_id.id if self.technician_id else False,
            'schedule_date': fields.Datetime.now(),
            'stage_id': first_stage.id,
            'si_schedule_id': self.id,
        })
        self.last_run_date = fields.Date.today()
        self._advance_next_run()
        return req

    def _advance_next_run(self):
        for sched in self:
            delta = {
                'daily': timedelta(days=sched.frequency_interval),
                'weekly': timedelta(weeks=sched.frequency_interval),
                'monthly': timedelta(days=30 * sched.frequency_interval),
                'quarterly': timedelta(days=90 * sched.frequency_interval),
                'yearly': timedelta(days=365 * sched.frequency_interval),
            }.get(sched.frequency)
            if delta:
                sched.next_run_date = sched.next_run_date + delta

    @api.model
    def _cron_generate_preventive(self):
        """Daily: generate maintenance requests for all due schedules."""
        today = fields.Date.today()
        due = self.search([
            ('active', '=', True),
            ('next_run_date', '<=', today),
        ])
        for sched in due:
            try:
                sched._generate_request()
            except Exception as e:  # noqa: BLE001
                sched.message_post(body=f'⚠️ Napaka pri generiranju zahtevka: {e}')


# Extend maintenance.request with link back to schedule
class MaintenanceRequestScheduleLink(models.Model):
    _inherit = 'maintenance.request'

    si_schedule_id = fields.Many2one(
        'l10n_si.maintenance.schedule', string='Preventive Schedule',
        readonly=True, copy=False,
    )
