# -*- coding: utf-8 -*-
"""Hall = posamezna dvorana znotraj venue-a."""
from odoo import fields, models


class L10nSiEventHall(models.Model):
    _name = 'l10n_si.event.hall'
    _description = 'Slovenian Event Hall'
    _inherit = ['mail.thread']
    _order = 'venue_id, sequence, name'

    name = fields.Char(required=True, translate=True, tracking=True)
    code = fields.Char(required=True, size=8)
    sequence = fields.Integer(default=10)
    active = fields.Boolean(default=True)
    venue_id = fields.Many2one('l10n_si.event.venue', required=True, ondelete='cascade')
    company_id = fields.Many2one(
        'res.company', related='venue_id.company_id', store=True,
    )

    # Kapaciteta
    capacity = fields.Integer(string='Kapaciteta (stoje)', default=100, required=True)
    capacity_seated = fields.Integer(string='Kapaciteta (sedež)', default=60,
                                       help='Pri banketih/slovesnostih.')
    capacity_classroom = fields.Integer(string='Kapaciteta (razred)', default=40,
                                          help='Konferenčna oblika.')
    size_sqm = fields.Float(string='Velikost (m²)')

    # Tip dvorane
    hall_type = fields.Selection(
        selection=[('ballroom', 'Poročna dvorana'),
                   ('conference', 'Konferenčna dvorana'),
                   ('meeting', 'Sejna soba'),
                   ('outdoor', 'Zunanji prostor'),
                   ('terrace', 'Terasa'),
                   ('vip', 'VIP salon'),
                   ('multi', 'Večnamenska')],
        default='multi',
        required=True,
    )

    # Cenik najema
    hourly_rate = fields.Float(string='Cena najema (EUR/h)', default=50.0)
    daily_rate = fields.Float(string='Cena najema (EUR/dan)', default=400.0)
    half_day_rate = fields.Float(string='Cena najema (pol dan)', default=250.0)
    min_booking_hours = fields.Integer(string='Min. najem (ure)', default=4)

    # Oprema vključena v ceno
    has_projector = fields.Boolean(default=True)
    has_screen = fields.Boolean(default=True)
    has_microphone = fields.Boolean(default=True)
    has_sound_system = fields.Boolean(default=True)
    has_stage = fields.Boolean(default=False)
    has_bar = fields.Boolean(default=True)
    has_kitchen_access = fields.Boolean(string='Dostop do kuhinje', default=False)

    # Status
    state = fields.Selection(
        selection=[('available', 'Prosta'),
                   ('booked', 'Zasedena'),
                   ('maintenance', 'Vzdrževanje')],
        default='available',
        tracking=True,
    )

    # Opis
    description = fields.Html()
    image = fields.Binary()
    floor_plan = fields.Binary(string='Tloris')

    booking_ids = fields.One2many('l10n_si.event.booking', 'hall_id', string='Rezervacije')

    def is_available(self, date_from, date_to, exclude_booking_id=False):
        """Preveri razpoložljivost dvorane v danem časovnem oknu."""
        self.ensure_one()
        domain = [
            ('hall_id', '=', self.id),
            ('state', 'in', ['confirmed', 'deposit_paid', 'in_progress', 'completed_pending']),
            ('date_from', '<', date_to),
            ('date_to', '>', date_from),
        ]
        if exclude_booking_id:
            domain.append(('id', '!=', exclude_booking_id))
        overlapping = self.env['l10n_si.event.booking'].search(domain)
        return not overlapping

    def action_set_available(self):
        self.write({'state': 'available'})

    def action_set_maintenance(self):
        self.write({'state': 'maintenance'})
