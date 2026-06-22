# -*- coding: utf-8 -*-
"""Loyalty reward - what member can redeem points for."""
from odoo import fields, models


class L10nSiLoyaltyReward(models.Model):
    _name = 'l10n_si.loyalty.reward'
    _description = 'Slovenian Loyalty Reward'
    _order = 'points_required'

    name = fields.Char(required=True, translate=True)
    active = fields.Boolean(default=True)
    points_required = fields.Integer(required=True, default=500,
                                       string='Točk za odkup')
    reward_type = fields.Selection(
        selection=[('free_night', 'Brezplačna nočitev'),
                   ('free_breakfast', 'Brezplačni zajtrk'),
                   ('free_dinner', 'Brezplačna večerja'),
                   ('free_wellness', 'Brezplačna masaža/wellness'),
                   ('room_upgrade', 'Upgrade sobe'),
                   ('discount_voucher', 'Vavčer za popust'),
                   ('gift', 'Darilo')],
        default='free_night',
        required=True,
    )
    description = fields.Text()
    image = fields.Binary()

    # Conditions
    valid_for_room_type_id = fields.Many2one('l10n_si.hotel.room.type',
                                              string='Veljavno za vrsto sobe')
    valid_days = fields.Selection(
        selection=[('any', 'Vsi dnevi'),
                   ('weekday', 'Samo delavni dnevi'),
                   ('weekend', 'Samo vikend'),
                   ('off_season', 'Samo izven sezone')],
        default='any',
    )
    expires_in_days = fields.Integer(default=365,
                                       string='Veljavnost po odkupu (dni)')

    # Available
    quantity_available = fields.Integer(default=-1, string='Na zalogi (-1 = neomejeno)')
    quantity_redeemed = fields.Integer(default=0, string='Že odkupljeno')

    company_id = fields.Many2one(
        'res.company', string='Company',
        default=lambda self: self.env.company, required=True,
    )
