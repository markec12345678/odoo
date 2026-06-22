# -*- coding: utf-8 -*-
"""Kamp parcele - tent, RV, cabin, glamping."""
from odoo import api, fields, models


class L10nSiCampingParcel(models.Model):
    _name = 'l10n_si.camping.parcel'
    _description = 'Slovenian Camping Parcel'
    _inherit = ['mail.thread']
    _order = 'zone, number'

    name = fields.Char(compute='_compute_name', store=True)
    number = fields.Char(required=True, size=10)
    zone = fields.Selection(
        selection=[('a', 'Cona A (ob morju/reki)'),
                   ('b', 'Cona B (srednja)'),
                   ('c', 'Cona C (zadaj)'),
                   ('sanitary', 'Sanitarna cona')],
        default='b',
        required=True,
    )
    parcel_type = fields.Selection(
        selection=[('tent', 'Šotor'),
                   ('rv', 'Avtodom/prikolica'),
                   ('cabin', 'Bungalov'),
                   ('glamping', 'Glamping'),
                   ('sanitary_block', 'Sanitarni blok')],
        default='tent',
        required=True,
    )

    # Capacity
    max_persons = fields.Integer(default=4)
    max_tents = fields.Integer(default=1)
    has_electricity = fields.Boolean(default=True)
    has_water = fields.Boolean(default=False)
    has_sewage = fields.Boolean(default=False, help='Priključek na kanalizacijo')
    size_sqm = fields.Float(string='Velikost (m²)')

    # Pricing base
    base_price = fields.Float(string='Osnovna cena (EUR/noč)', default=20.0)
    extra_person_price = fields.Float(string='Dodatna oseba (EUR)', default=5.0)
    electricity_price = fields.Float(string='Elektrika (EUR/dan)', default=3.0)

    # Status
    state = fields.Selection(
        selection=[('available', 'Prosta'),
                   ('occupied', 'Zasedena'),
                   ('reserved', 'Rezervirana'),
                   ('maintenance', 'Vzdrževanje')],
        default='available',
        tracking=True,
    )
    active = fields.Boolean(default=True)
    image = fields.Binary()

    # Long-stay discount
    long_stay_discount_days = fields.Integer(default=7, help='Po N dneh uporabi popust')
    long_stay_discount_percent = fields.Float(default=10.0, help='Popust v %')

    company_id = fields.Many2one(
        'res.company', string='Company',
        default=lambda self: self.env.company, required=True,
    )

    reservation_ids = fields.One2many('l10n_si.camping.reservation', 'parcel_id', string='Rezervacije')

    @api.depends('number', 'zone')
    def _compute_name(self):
        for p in self:
            p.name = f'{p.zone.upper()}-{p.number}'

    def is_available(self, date_from, date_to):
        self.ensure_one()
        overlapping = self.env['l10n_si.camping.reservation'].search([
            ('parcel_id', '=', self.id),
            ('state', 'in', ['confirmed', 'checked_in']),
            ('check_in', '<', date_to),
            ('check_out', '>', date_from),
        ])
        return not overlapping

    def action_set_available(self):
        self.write({'state': 'available'})

    def action_set_maintenance(self):
        self.write({'state': 'maintenance'})
