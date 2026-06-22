# -*- coding: utf-8 -*-
"""Mize - restaurant tables with floor plan."""
from odoo import api, fields, models


class L10nSiRestaurantTable(models.Model):
    _name = 'l10n_si.restaurant.table'
    _description = 'Slovenian Restaurant Table'
    _order = 'floor, number'

    name = fields.Char(compute='_compute_name', store=True)
    number = fields.Char(required=True, size=4)
    floor = fields.Selection(
        selection=[('indoor', 'Notranja'),
                   ('outdoor', 'Terasa'),
                   ('vip', 'VIP'),
                   ('bar', 'Bar')],
        default='indoor',
        required=True,
    )
    capacity = fields.Integer(default=4, required=True)
    shape = fields.Selection(
        selection=[('round', 'Okrogla'),
                   ('square', 'Kvadratna'),
                   ('rectangular', 'Pravokotna')],
        default='square',
    )
    state = fields.Selection(
        selection=[('free', 'Prosta'),
                   ('occupied', 'Zasedena'),
                   ('reserved', 'Rezervirana'),
                   ('cleaning', 'Čiščenje')],
        default='free',
        tracking=True,
    )
    active = fields.Boolean(default=True)

    # Position on floor plan (x, y in %)
    pos_x = fields.Float(default=0.0)
    pos_y = fields.Float(default=0.0)

    # Current occupancy
    current_kot_id = fields.Many2one('l10n_si.restaurant.kot', string='Trenutni KOT', readonly=True, copy=False)
    current_guests = fields.Integer(related='current_kot_id.guests', string='Gostje')
    opened_at = fields.Datetime(related='current_kot_id.create_date', string='Odprto ob')

    company_id = fields.Many2one(
        'res.company', string='Company',
        default=lambda self: self.env.company, required=True,
    )

    _sql_constraints = [
        ('number_company_uniq', 'unique(number, company_id)', 'Table number must be unique per company.'),
    ]

    @api.depends('number', 'floor')
    def _compute_name(self):
        floor_labels = {'indoor': 'I', 'outdoor': 'T', 'vip': 'V', 'bar': 'B'}
        for t in self:
            prefix = floor_labels.get(t.floor, 'X')
            t.name = f'{prefix}-{t.number}'

    def action_occupy(self):
        self.write({'state': 'occupied'})

    def action_free(self):
        self.write({'state': 'free', 'current_kot_id': False})

    def action_cleaning(self):
        self.write({'state': 'cleaning'})

    def action_reserve(self):
        self.write({'state': 'reserved'})
