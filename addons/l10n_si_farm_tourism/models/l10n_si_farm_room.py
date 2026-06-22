# -*- coding: utf-8 -*-
"""Sobe na kmetiji - tipično 5-15 ležišč."""
from odoo import api, fields, models


class L10nSiFarmRoom(models.Model):
    _name = 'l10n_si.farm.room'
    _description = 'Slovenian Farm Room'
    _order = 'name'

    name = fields.Char(required=True, translate=True)
    number = fields.Char(required=True, size=4)
    beds = fields.Integer(string='Ležišča', default=2, required=True)
    extra_beds = fields.Integer(default=0)
    has_private_bathroom = fields.Boolean(string='Lastna kopalnica', default=True)
    has_kitchen_access = fields.Boolean(string='Skupna kuhinja', default=True)

    # Pricing
    price_per_night = fields.Float(string='Cena/noč (EUR)', default=35.0)
    breakfast_included = fields.Boolean(default=True)
    breakfast_price = fields.Float(string='Zajtrk (EUR/oseba)', default=8.0)

    # Status
    state = fields.Selection(
        selection=[('available', 'Prosta'),
                   ('occupied', 'Zasedena'),
                   ('reserved', 'Rezervirana'),
                   ('cleaning', 'Čiščenje')],
        default='available',
    )
    active = fields.Boolean(default=True)

    # Reservation count
    reservation_count = fields.Integer(compute='_compute_count', store=False)

    company_id = fields.Many2one(
        'res.company', string='Company',
        default=lambda self: self.env.company, required=True,
    )

    def _compute_count(self):
        Reservation = self.env['l10n_si.farm.reservation']
        for room in self:
            room.reservation_count = Reservation.search_count([
                ('room_id', '=', room.id),
                ('state', 'in', ['confirmed', 'checked_in']),
            ])

    def is_available(self, date_from, date_to):
        self.ensure_one()
        overlapping = self.env['l10n_si.farm.reservation'].search([
            ('room_id', '=', self.id),
            ('state', 'in', ['confirmed', 'checked_in']),
            ('check_in', '<', date_to),
            ('check_out', '>', date_from),
        ])
        return not overlapping
