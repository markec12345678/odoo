# -*- coding: utf-8 -*-
"""Mapping between SI room types and channel room types."""
from odoo import fields, models


class L10nSiChannelRoomMapping(models.Model):
    _name = 'l10n_si.channel.room.mapping'
    _description = 'Slovenian Channel Room Mapping'
    _order = 'channel_config_id, room_type_id'

    channel_config_id = fields.Many2one('l10n_si.channel.config', required=True, ondelete='cascade')
    company_id = fields.Many2one(related='channel_config_id.company_id', store=True)

    # SI side
    si_model = fields.Selection(
        selection=[('hotel', 'Hotel (l10n_si.hotel.room.type)'),
                   ('camping', 'Camping (l10n_si.camping.parcel)')],
        default='hotel',
        required=True,
    )
    room_type_id = fields.Many2one('l10n_si.hotel.room.type',
                                     string='Hotel room type')
    parcel_id = fields.Many2one('l10n_si.camping.parcel',
                                  string='Kamp parcela')

    # Channel side
    channel_room_type_id = fields.Char(required=True, string='Channel room type ID')
    channel_room_type_name = fields.Char(string='Ime na kanalu')

    # Pricing
    price_override = fields.Float(string='Fiksna cena (EUR)', default=0.0,
                                    help='0 = uporabi SI ceno + markup iz channel config.')
    min_stay_nights = fields.Integer(default=1, string='Min. nočitev')
    max_stay_nights = fields.Integer(default=30, string='Max. nočitev')

    active = fields.Boolean(default=True)

    def get_si_record(self):
        """Return the actual SI record (hotel room type or camping parcel)."""
        self.ensure_one()
        if self.si_model == 'hotel':
            return self.room_type_id
        elif self.si_model == 'camping':
            return self.parcel_id
        return False
