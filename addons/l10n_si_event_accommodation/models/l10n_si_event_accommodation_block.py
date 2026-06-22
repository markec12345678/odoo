# -*- coding: utf-8 -*-
"""Block reservation of rooms for one event."""
from odoo import api, fields, models


class L10nSiEventAccommodationBlock(models.Model):
    _name = 'l10n_si.event.accommodation.block'
    _description = 'Slovenian Event Accommodation Block'
    _inherit = ['mail.thread']
    _order = 'date_from DESC'

    name = fields.Char(compute='_compute_name', store=True)
    event_id = fields.Many2one('l10n_si.event.event', required=True, ondelete='cascade')
    company_id = fields.Many2one('res.company', related='event_id.company_id', store=True)

    # Block dates
    date_from = fields.Date(required=True)
    date_to = fields.Date(required=True)
    release_date = fields.Date(
        required=True,
        help='Do tega datuma lahko goste rezervira po posebni ceni.',
    )

    # Rooms
    room_type_id = fields.Many2one('l10n_si.hotel.room.type', required=True)
    room_ids = fields.Many2many('l10n_si.hotel.room', string='Blokirane sobe')
    blocked_room_count = fields.Integer(compute='_compute_count', store=False)

    # Pricing
    special_rate = fields.Float(required=True, default=70.0,
                                  help='Special price per night for event guests.')
    standard_rate = fields.Float(related='room_type_id.list_price', store=False)

    # Status
    state = fields.Selection(
        selection=[('draft', 'Osnutek'),
                   ('active', 'Aktiven'),
                   ('released', 'Sproščen'),
                   ('expired', 'Potekel')],
        default='draft',
        tracking=True,
    )

    reservation_ids = fields.One2many(
        'l10n_si.event.accommodation.reservation', 'block_id', string='Rezervacije gostov',
    )
    reservation_count = fields.Integer(compute='_compute_count', store=False)
    available_rooms = fields.Integer(compute='_compute_count', store=False)

    @api.depends('event_id.name', 'room_type_id.name')
    def _compute_name(self):
        for b in self:
            b.name = f'{b.event_id.name} - {b.room_type_id.name or ""}'

    def _compute_count(self):
        for b in self:
            b.blocked_room_count = len(b.room_ids)
            b.reservation_count = len(b.reservation_ids)
            booked = len(b.reservation_ids.filtered(lambda r: r.state in ['confirmed', 'checked_in']))
            b.available_rooms = b.blocked_room_count - booked

    def action_activate(self):
        self.write({'state': 'active'})

    def action_release(self):
        """Sprosti neporabljene sobe nazaj v splošno zalogo."""
        self.write({'state': 'released'})
