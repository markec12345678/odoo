# -*- coding: utf-8 -*-
"""Occupancy forecast - napoved zasedenosti za naslednje dni."""
from odoo import api, fields, models


class L10nSiOccupancyForecast(models.Model):
    _name = 'l10n_si.occupancy.forecast'
    _description = 'Slovenian Occupancy Forecast'
    _order = 'date'

    date = fields.Date(required=True)
    company_id = fields.Many2one(
        'res.company', string='Company',
        default=lambda self: self.env.company, required=True,
    )

    # Current state
    total_rooms = fields.Integer(readonly=True)
    confirmed_bookings = fields.Integer(readonly=True, string='Potrjene rezervacije')
    tentative_bookings = fields.Integer(readonly=True, string='Tentative rezervacije')
    forecasted_occupancy = fields.Float(string='Napovedana zasedenost (%)', readonly=True)
    actual_occupancy = fields.Float(string='Dejanska zasedenost (%)', readonly=True)
    variance = fields.Float(compute='_compute_variance', store=False,
                              string='Odklon (%)')

    # Prediction metadata
    forecast_method = fields.Selection(
        selection=[('manual', 'Ročno'),
                   ('historical', 'Glede na zgodovino'),
                   ('ai', 'AI napoved')],
        default='historical', readonly=True,
    )
    forecast_on = fields.Datetime(readonly=True)
    notes = fields.Text()

    @api.depends('forecasted_occupancy', 'actual_occupancy')
    def _compute_variance(self):
        for f in self:
            if f.forecasted_occupancy:
                f.variance = f.actual_occupancy - f.forecasted_occupancy
            else:
                f.variance = 0.0

    @api.model
    def _cron_generate_forecast(self):
        """Generate forecast for next 30 days based on current bookings + historical pattern."""
        from datetime import date, timedelta
        today = date.today()
        for i in range(30):
            target = today + timedelta(days=i)
            existing = self.search([('date', '=', target), ('company_id', '=', self.env.company.id)], limit=1)
            if not existing:
                existing = self.create({
                    'date': target,
                    'company_id': self.env.company.id,
                    'forecast_method': 'historical',
                    'forecast_on': fields.Datetime.now(),
                })
            # Compute forecast
            existing._compute_forecast()

    def _compute_forecast(self):
        """Compute forecast based on historical + current bookings."""
        for f in self:
            total = self.env['l10n_si.hotel.room'].search_count([
                ('active', '=', True),
                ('company_id', '=', f.company_id.id),
            ])
            f.total_rooms = total

            # Confirmed bookings for this date
            confirmed = 0
            for room in self.env['l10n_si.hotel.room'].search([('active', '=', True)]):
                overlapping = self.env['l10n_si.hotel.reservation'].search_count([
                    ('room_id', '=', room.id),
                    ('state', 'in', ['confirmed', 'checked_in']),
                    ('check_in', '<=', f.date.strftime('%Y-%m-%d 23:59:59')),
                    ('check_out', '>', f.date.strftime('%Y-%m-%d 00:00:00')),
                ])
                if overlapping:
                    confirmed += 1
            f.confirmed_bookings = confirmed
            # Add historical bump (typically +15% last-minute bookings)
            forecasted = min(confirmed * 1.15, total) if total else 0
            f.forecasted_occupancy = (forecasted / total * 100) if total else 0
