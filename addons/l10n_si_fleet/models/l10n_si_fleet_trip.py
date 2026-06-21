# -*- coding: utf-8 -*-
"""Trip log — vozni list."""
from odoo import api, fields, models


class L10nSiFleetTrip(models.Model):
    _name = 'l10n_si.fleet.trip'
    _description = 'Slovenian Fleet Trip (Vozni list)'
    _inherit = ['mail.thread']
    _order = 'date_start DESC'

    name = fields.Char(compute='_compute_name', store=True)
    vehicle_id = fields.Many2one('fleet.vehicle', required=True, ondelete='restrict')
    driver_id = fields.Many2one('hr.employee', string='Voznik', required=True)
    date_start = fields.Datetime(string='Začetek', required=True, default=fields.Datetime.now)
    date_end = fields.Datetime(string='Konec')
    mileage_start = fields.Integer(string='Stanje števca (start)', required=True)
    mileage_end = fields.Integer(string='Stanje števca (konec)')
    distance = fields.Integer(
        string='Prevoženi kilometri',
        compute='_compute_distance', store=True,
    )
    purpose = fields.Selection(
        selection=[('poslovno', 'Poslovno'),
                   ('zasebno', 'Zasebno'),
                   ('sluzbeno', 'Službeno (med kraji dela)')],
        default='poslovno',
        required=True,
    )
    description = fields.Text(string='Opis vožnje')
    partner_id = fields.Many2one('res.partner', string='Stranka')
    company_id = fields.Many2one(
        'res.company', string='Company',
        default=lambda self: self.env.company, required=True,
    )

    @api.depends('vehicle_id', 'date_start')
    def _compute_name(self):
        for trip in self:
            trip.name = f'{trip.vehicle_id.name or ""} - {trip.date_start or ""}'

    @api.depends('mileage_start', 'mileage_end')
    def _compute_distance(self):
        for trip in self:
            if trip.mileage_end and trip.mileage_start:
                trip.distance = trip.mileage_end - trip.mileage_start
            else:
                trip.distance = 0

    def action_end_trip(self):
        for trip in self:
            trip.date_end = fields.Datetime.now()
