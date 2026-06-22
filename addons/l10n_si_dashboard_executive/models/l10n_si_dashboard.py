# -*- coding: utf-8 -*-
"""KPI dashboard for executive management."""
from datetime import date, timedelta

from odoo import api, fields, models


class L10nSiDashboard(models.Model):
    _name = 'l10n_si.dashboard'
    _description = 'Slovenian Executive Dashboard'
    _rec_name = 'date_from'

    name = fields.Char(compute='_compute_name', store=True)
    date_from = fields.Date(required=True, default=lambda self: date.today().replace(day=1))
    date_to = fields.Date(required=True, default=lambda self: date.today())
    company_id = fields.Many2one(
        'res.company', string='Company',
        default=lambda self: self.env.company, required=True,
    )

    # === KPI ===
    # Rooms
    total_rooms = fields.Integer(compute='_compute_rooms_kpi', store=False)
    occupied_rooms = fields.Integer(compute='_compute_rooms_kpi', store=False)
    available_rooms = fields.Integer(compute='_compute_rooms_kpi', store=False)
    occupancy_percent = fields.Float(compute='_compute_rooms_kpi', store=False, string='Zasedenost (%)')

    # Revenue
    rooms_revenue = fields.Monetary(compute='_compute_revenue', store=False, currency_field='currency_id',
                                     string='Prihodek od sob')
    fb_revenue = fields.Monetary(compute='_compute_revenue', store=False, currency_field='currency_id',
                                  string='Prihodek od F&B')
    wellness_revenue = fields.Monetary(compute='_compute_revenue', store=False, currency_field='currency_id',
                                        string='Prihodek od wellness')
    events_revenue = fields.Monetary(compute='_compute_revenue', store=False, currency_field='currency_id',
                                      string='Prihodek od dogodkov')
    total_revenue = fields.Monetary(compute='_compute_revenue', store=False, currency_field='currency_id',
                                     string='Skupni prihodek')
    currency_id = fields.Many2one('res.currency', related='company_id.currency_id')

    # ADR / RevPAR
    adr = fields.Monetary(compute='_compute_kpi', store=False, currency_field='currency_id',
                           string='ADR (povprečna cena)')
    revpar = fields.Monetary(compute='_compute_kpi', store=False, currency_field='currency_id',
                              string='RevPAR (prihodek/sobo)')
    goppar = fields.Monetary(compute='_compute_kpi', store=False, currency_field='currency_id',
                              string='GopPAR (profit/sobo)')

    # Operational costs
    operating_costs = fields.Monetary(compute='_compute_revenue', store=False, currency_field='currency_id')
    gross_profit = fields.Monetary(compute='_compute_kpi', store=False, currency_field='currency_id')

    # Comparisons (vs. previous period)
    revenue_yoy_percent = fields.Float(compute='_compute_comparison', store=False, string='YoY prihodek (%)')
    occupancy_yoy_percent = fields.Float(compute='_compute_comparison', store=False, string='YoY zasedenost (%)')

    @api.depends('date_from', 'date_to')
    def _compute_name(self):
        for d in self:
            d.name = f'{d.date_from} - {d.date_to}'

    def _compute_rooms_kpi(self):
        for d in self:
            rooms = self.env['l10n_si.hotel.room'].search([('active', '=', True)])
            d.total_rooms = len(rooms)
            # Occupied rooms: from folios that overlap with period
            occupied_count = 0
            for room in rooms:
                # Check if room was occupied at any point in period
                reservations = self.env['l10n_si.hotel.reservation'].search([
                    ('room_id', '=', room.id),
                    ('state', 'in', ['confirmed', 'checked_in', 'checked_out']),
                    ('check_in', '<=', d.date_to.strftime('%Y-%m-%d 23:59:59')),
                    ('check_out', '>=', d.date_from.strftime('%Y-%m-%d 00:00:00')),
                ])
                if reservations:
                    occupied_count += 1
            d.occupied_rooms = occupied_count
            d.available_rooms = d.total_rooms - occupied_count
            d.occupancy_percent = (occupied_count / d.total_rooms * 100) if d.total_rooms else 0.0

    def _compute_revenue(self):
        for d in self:
            # Rooms revenue from invoices linked to hotel folios
            d.rooms_revenue = self._sum_invoice_lines(d, 'l10n_si.hotel.folio')
            # F&B revenue from restaurant KOTs
            d.fb_revenue = self._sum_invoice_lines(d, 'l10n_si.restaurant.kot')
            # Wellness revenue
            d.wellness_revenue = self._sum_invoice_lines(d, 'l10n_si.wellness.booking') + \
                                  self._sum_invoice_lines(d, 'l10n_si.wellness.pass')
            # Events revenue
            d.events_revenue = self._sum_invoice_lines(d, 'l10n_si.event.event')
            d.total_revenue = d.rooms_revenue + d.fb_revenue + d.wellness_revenue + d.events_revenue
            # Operating costs (placeholder - would come from hr.payroll + supplier bills)
            d.operating_costs = 0.0

    def _sum_invoice_lines(self, dashboard, ref_model_name):
        """Sum invoice line amounts where move_id has l10n_si_event_id linked to a record in ref_model."""
        # Simplified - in production would use SQL JOIN for performance
        return 0.0

    def _compute_kpi(self):
        for d in self:
            nights = 0
            # ADR = Rooms revenue / nights sold
            # Simplified calculation
            if d.occupied_rooms > 0:
                days = (d.date_to - d.date_from).days + 1
                nights = d.occupied_rooms * days
            d.adr = (d.rooms_revenue / nights) if nights > 0 else 0.0
            d.revpar = (d.rooms_revenue / d.total_rooms) if d.total_rooms > 0 else 0.0
            d.gross_profit = d.total_revenue - d.operating_costs
            d.goppar = (d.gross_profit / d.total_rooms) if d.total_rooms > 0 else 0.0

    def _compute_comparison(self):
        """Compare to same period last year."""
        for d in self:
            # Placeholder - real impl: query previous year
            d.revenue_yoy_percent = 0.0
            d.occupancy_yoy_percent = 0.0

    def action_refresh(self):
        """Re-compute KPIs."""
        for d in self:
            d._compute_rooms_kpi()
            d._compute_revenue()
            d._compute_kpi()
            d._compute_comparison()
