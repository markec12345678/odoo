# -*- coding: utf-8 -*-
from odoo import api, fields, models


class HotelRoomType(models.Model):
    """Vrsta sobe - npr. Standard, Deluxe, Suite, Family."""
    _name = 'l10n_si.hotel.room.type'
    _description = 'Slovenian Hotel Room Type'
    _order = 'sequence, name'

    name = fields.Char(required=True, translate=True)
    sequence = fields.Integer(default=10)
    code = fields.Char(required=True, size=8, help='Short code (STD, DLX, SUITE)')
    active = fields.Boolean(default=True)
    company_id = fields.Many2one(
        'res.company', string='Company',
        default=lambda self: self.env.company, required=True,
    )

    # Pricing
    list_price = fields.Float(string='Osnovna cena (EUR)', default=80.0)
    weekend_premium = fields.Float(
        string='Vikend dodatek (%)', default=10.0,
        help='Percentage added Fri-Sun.',
    )
    seasonal_multiplier = fields.Float(
        string='Sezonski faktor', default=1.0,
        help='Multiply base price in high season (e.g. 1.5 = +50%).',
    )

    # Capacity
    capacity_adults = fields.Integer(default=2)
    capacity_children = fields.Integer(default=0)
    capacity_extra_beds = fields.Integer(default=0)
    size_sqm = fields.Float(string='Velikost (m²)')

    # Description
    description = fields.Html()
    image = fields.Binary()
    amenity_ids = fields.Many2many('l10n_si.hotel.amenity', string='Oprema')

    room_ids = fields.One2many('l10n_si.hotel.room', 'room_type_id', string='Sobe')

    _sql_constraints = [
        ('code_company_uniq', 'unique(code, company_id)', 'Code must be unique per company.'),
    ]


class L10nSiHotelAmenity(models.Model):
    """Oprema sobe - TV, WiFi, minibar, klima, ..."""
    _name = 'l10n_si.hotel.amenity'
    _description = 'Slovenian Hotel Amenity'

    name = fields.Char(required=True, translate=True)
    code = fields.Char(required=True, size=16)
    icon = fields.Char(help='FontAwesome icon class, e.g. fa-wifi')
    active = fields.Boolean(default=True)
