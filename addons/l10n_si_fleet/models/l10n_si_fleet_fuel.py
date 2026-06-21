# -*- coding: utf-8 -*-
"""Fuel log — točenje goriva."""
from odoo import api, fields, models


class L10nSiFleetFuel(models.Model):
    _name = 'l10n_si.fleet.fuel'
    _description = 'Slovenian Fleet Fuel Log'
    _order = 'date DESC'

    name = fields.Char(compute='_compute_name', store=True)
    vehicle_id = fields.Many2one('fleet.vehicle', required=True, ondelete='restrict')
    driver_id = fields.Many2one('hr.employee', string='Voznik')
    date = fields.Datetime(required=True, default=fields.Datetime.now)
    fuel_type = fields.Selection(
        selection=[('bencin', 'Bencin'),
                   ('dizel', 'Dizel'),
                   ('elektricni', 'Električni'),
                   ('plin', 'Plin')],
        required=True,
        default='dizel',
    )
    volume = fields.Float(string='Količina (l ali kWh)', required=True)
    price_per_unit = fields.Float(string='Cena na enoto (€)', required=True)
    total_cost = fields.Float(
        string='Skupaj (€)', compute='_compute_total', store=True,
    )
    odometer = fields.Integer(string='Stanje števca (km)')
    fuel_station = fields.Char(string='Bencinska črpalka')
    invoice_number = fields.Char(string='Številka računa')
    company_id = fields.Many2one(
        'res.company', string='Company',
        default=lambda self: self.env.company, required=True,
    )

    @api.depends('vehicle_id', 'date')
    def _compute_name(self):
        for log in self:
            log.name = f'{log.vehicle_id.name or ""} - {log.date or ""}'

    @api.depends('volume', 'price_per_unit')
    def _compute_total(self):
        for log in self:
            log.total_cost = log.volume * log.price_per_unit
