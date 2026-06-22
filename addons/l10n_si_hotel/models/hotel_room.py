# -*- coding: utf-8 -*-
from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class HotelRoom(models.Model):
    """Posamezna soba v hotelu."""
    _name = 'l10n_si.hotel.room'
    _description = 'Slovenian Hotel Room'
    _inherit = ['mail.thread']
    _order = 'floor, number'

    name = fields.Char(compute='_compute_name', store=True)
    number = fields.Char(required=True, size=10, help='Številka sobe (101, 102, ...)')
    floor = fields.Integer(default=1)
    room_type_id = fields.Many2one('l10n_si.hotel.room.type', required=True, ondelete='restrict')
    company_id = fields.Many2one(
        'res.company', string='Company',
        default=lambda self: self.env.company, required=True,
    )

    # Status
    state = fields.Selection(
        selection=[('available', 'Prosta'),
                   ('occupied', 'Zasedena'),
                   ('reserved', 'Rezervirana'),
                   ('cleaning', 'Čiščenje'),
                   ('out_of_order', 'Vzdrževanje')],
        default='available',
        tracking=True,
    )
    active = fields.Boolean(default=True)

    # Current occupancy
    current_folio_id = fields.Many2one('l10n_si.hotel.folio', string='Trenutni folio', readonly=True, copy=False)
    current_guest_name = fields.Char(related='current_folio_id.partner_id.name', string='Trenutni gost')

    # Reservations referencing this room
    reservation_ids = fields.One2many('l10n_si.hotel.reservation', 'room_id', string='Rezervacije')

    _sql_constraints = [
        ('number_company_uniq', 'unique(number, company_id)', 'Room number must be unique per company.'),
    ]

    @api.depends('number', 'room_type_id.code')
    def _compute_name(self):
        for room in self:
            code = room.room_type_id.code or ''
            room.name = f'{code}-{room.number}' if code else room.number

    def action_set_available(self):
        self.write({'state': 'available', 'current_folio_id': False})

    def action_set_cleaning(self):
        self.write({'state': 'cleaning'})

    def action_set_out_of_order(self):
        self.write({'state': 'out_of_order'})

    @api.constrains('number')
    def _check_number(self):
        for room in self:
            if not room.number or not room.number.strip():
                raise ValidationError(_('Room number cannot be empty.'))

    def is_available(self, date_from, date_to):
        """Check if room is available between two dates (exclusive of check-out)."""
        self.ensure_one()
        overlapping = self.env['l10n_si.hotel.reservation'].search([
            ('room_id', '=', self.id),
            ('state', 'in', ['confirmed', 'checked_in']),
            ('check_in', '<', date_to),
            ('check_out', '>', date_from),
        ])
        return not overlapping
