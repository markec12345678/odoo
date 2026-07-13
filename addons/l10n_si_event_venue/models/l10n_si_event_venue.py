# -*- coding: utf-8 -*-
"""Venue = lokacija dogodka (npr. Grand Hotel, Kongresni center)."""
from odoo import fields, models


class L10nSiEventVenue(models.Model):
    _name = 'l10n_si.event.venue'
    _description = 'Slovenian Event Venue'
    _inherit = ['mail.thread']
    _order = 'name'

    name = fields.Char(required=True, translate=True, tracking=True)
    code = fields.Char(required=True, size=16)
    active = fields.Boolean(default=True)
    partner_id = fields.Many2one(
        'res.partner', string='Lastnik/Partner',
        help='Lastnik venue-a (npr. hotelska družba).',
    )
    company_id = fields.Many2one(
        'res.company', string='Company',
        default=lambda self: self.env.company, required=True,
    )

    # Lokacija
    street = fields.Char()
    street2 = fields.Char()
    zip = fields.Char(string='Poštna št.')
    city = fields.Char()
    country_id = fields.Many2one('res.country', default=lambda self: self.env.ref('base.si'))
    municipality_id = fields.Many2one('l10n_si.tourist.tax.municipality', string='Občina')

    # Kapaciteta
    hall_ids = fields.One2many('l10n_si.event.hall', 'venue_id', string='Dvorane')
    hall_count = fields.Integer(compute='_compute_count', store=False)
    total_capacity = fields.Integer(compute='_compute_count', store=False,
                                     help='Skupna kapaciteta vseh dvoran.')

    # kontakt
    contact_name = fields.Char(string='Kontakt oseba')
    contact_phone = fields.Char()
    contact_email = fields.Char()

    # Parkirišče
    parking_spaces = fields.Integer(string='Parkirna mesta', default=0)
    has_disabled_access = fields.Boolean(string='Dostop za invalide', default=True)
    has_wifi = fields.Boolean(string='Brezplačen WiFi', default=True)
    has_air_condition = fields.Boolean(string='Klima', default=True)

    # Opis
    description = fields.Html()
    image = fields.Binary()

    # Statistika
    event_count = fields.Integer(compute='_compute_count', store=False)

    def _compute_count(self):
        Event = self.env['l10n_si.event.event']
        for v in self:
            v.hall_count = len(v.hall_ids)
            v.total_capacity = sum(h.capacity for h in v.hall_ids)
            v.event_count = Event.search_count([('venue_id', '=', v.id)])

    _sql_constraints = [
        ('code_company_uniq', 'unique(code, company_id)', 'Venue code must be unique per company.'),
    ]

    def action_view_halls(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Dvorane',
            'res_model': 'l10n_si.event.hall',
            'view_mode': 'list,form',
            'domain': [('venue_id', '=', self.id)],
        }

    def action_view_events(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Dogodki',
            'res_model': 'l10n_si.event.event',
            'view_mode': 'list,form,calendar',
            'domain': [('venue_id', '=', self.id)],
        }
