# -*- coding: utf-8 -*-
"""Rate calendar - dnevne cene za naslednji 90 dni."""
from datetime import date, timedelta

from odoo import api, fields, models


class L10nSiRateCalendar(models.Model):
    _name = 'l10n_si.rate.calendar'
    _description = 'Slovenian Rate Calendar Entry'
    _order = 'date, rate_plan_id'
    _rec_name = 'date'

    date = fields.Date(required=True)
    rate_plan_id = fields.Many2one('l10n_si.rate.plan', required=True, ondelete='cascade')
    company_id = fields.Many2one(related='rate_plan_id.company_id', store=True)

    # Compute
    computed_rate = fields.Float(string='Izračunana cena (EUR)', readonly=True)
    applied_factors = fields.Text(readonly=True)
    occupancy_at_compute = fields.Float(string='Zasedenost ob izračunu (%)', readonly=True)

    # Override (ročno nastavljena cena)
    override_rate = fields.Float(string='Ročno nastavljena cena (EUR)', default=0.0,
                                   help='0 = uporabi izračunano ceno.')
    final_rate = fields.Float(compute='_compute_final', store=True, string='Končna cena')

    # Status
    state = fields.Selection(
        selection=[('draft', 'Osnutek'),
                   ('published', 'Objavljeno'),
                   ('closed', 'Zaprto')],
        default='draft',
    )

    # Omejitve za ta dan
    closed_to_arrival = fields.Boolean(default=False)
    closed_to_departure = fields.Boolean(default=False)
    min_los_override = fields.Integer(default=0, help='0 = uporabi privzeto iz rate plan')

    _sql_constraints = [
        ('date_rate_plan_uniq', 'unique(date, rate_plan_id)', 'Rate entry must be unique per date and rate plan.'),
    ]

    @api.depends('computed_rate', 'override_rate')
    def _compute_final(self):
        for r in self:
            r.final_rate = r.override_rate if r.override_rate > 0 else r.computed_rate

    def action_recompute(self):
        """Ponovno izračunaj cene na podlagi trenutne zasedenosti."""
        today = date.today()
        for entry in self:
            rate_plan = entry.rate_plan_id
            # Get current occupancy for this date
            occ = self._get_occupancy_for_date(entry.date)
            days_to_arrival = (entry.date - today).days
            rate, factors = rate_plan.compute_rate(entry.date, occ, days_to_arrival)
            entry.write({
                'computed_rate': rate,
                'applied_factors': '; '.join(factors),
                'occupancy_at_compute': occ,
            })

    def _get_occupancy_for_date(self, target_date):
        """Get occupancy percentage for a specific date from hotel reservations."""
        total_rooms = self.env['l10n_si.hotel.room'].search_count([('active', '=', True)])
        if not total_rooms:
            return 0.0
        # Count rooms with overlapping reservation
        occupied = 0
        rooms = self.env['l10n_si.hotel.room'].search([('active', '=', True)])
        for room in rooms:
            overlapping = self.env['l10n_si.hotel.reservation'].search_count([
                ('room_id', '=', room.id),
                ('state', 'in', ['confirmed', 'checked_in']),
                ('check_in', '<=', target_date.strftime('%Y-%m-%d 23:59:59')),
                ('check_out', '>', target_date.strftime('%Y-%m-%d 00:00:00')),
            ])
            if overlapping:
                occupied += 1
        return (occupied / total_rooms) * 100.0 if total_rooms else 0.0

    def action_publish(self):
        """Publish rates to channel manager."""
        self.write({'state': 'published'})

    def action_close(self):
        self.write({'state': 'closed'})

    @api.model
    def _cron_generate_calendar(self):
        """Daily: generate/update rate calendar entries for next 90 days."""
        today = date.today()
        rate_plans = self.env['l10n_si.rate.plan'].search([('active', '=', True)])
        for plan in rate_plans:
            for i in range(90):
                target = today + timedelta(days=i)
                existing = self.search([
                    ('date', '=', target),
                    ('rate_plan_id', '=', plan.id),
                ], limit=1)
                if not existing:
                    self.create({
                        'date': target,
                        'rate_plan_id': plan.id,
                    })
        # Recompute all draft entries
        self.search([('state', '=', 'draft')]).action_recompute()
