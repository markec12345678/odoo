# -*- coding: utf-8 -*-
"""Rooming list - which guest is in which room."""
from odoo import api, fields, models


class L10nSiRoomingList(models.Model):
    _name = 'l10n_si.rooming.list'
    _description = 'Slovenian Rooming List Entry'
    _order = 'room_number'

    group_booking_id = fields.Many2one('l10n_si.group.booking', required=True, ondelete='cascade')
    company_id = fields.Many2one(related='group_booking_id.company_id', store=True)

    # Gost v sobi
    partner_id = fields.Many2one('res.partner', string='Glavni gost')
    guest_name = fields.Char(string='Ime gosta', required=True,
                              help='Uporablja se kadar partner ni znan (samo ime)')
    guest_email = fields.Char()
    guest_phone = fields.Char()

    # Soba
    room_number = fields.Char(string='Številka sobe', required=True)
    room_id = fields.Many2one('l10n_si.hotel.room', string='Dodeljena soba (kadar znana)')
    room_type_id = fields.Many2one(related='group_booking_id.room_type_id', store=True)

    # Gostje v sobi
    adults = fields.Integer(default=2, required=True)
    children = fields.Integer(default=0)
    children_ages = fields.Char(string='Starosti otrok (npr. 5,8,12)')

    # Posebnosti
    special_requests = fields.Char(string='Posebne želje (npr. dve postelji)')
    is_leader = fields.Boolean(string='Vodja skupine', default=False)

    # Status
    state = fields.Selection(
        selection=[('assigned', 'Dodeljeno'),
                   ('checked_in', 'Prijavljen'),
                   ('checked_out', 'Odjavljen'),
                   ('changed', 'Spremenjeno'),
                   ('cancelled', 'Preklicano')],
        default='assigned',
        tracking=True,
    )

    # Povezava z rezervacijo/folio
    hotel_reservation_id = fields.Many2one('l10n_si.hotel.reservation', string='Povezana rezervacija')

    @api.onchange('partner_id')
    def _onchange_partner(self):
        if self.partner_id:
            self.guest_name = self.partner_id.name
            self.guest_email = self.partner_id.email
            self.guest_phone = self.partner_id.phone

    def action_check_in(self):
        for r in self:
            r.state = 'checked_in'

    def action_check_out(self):
        for r in self:
            r.state = 'checked_out'
