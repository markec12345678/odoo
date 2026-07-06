# -*- coding: utf-8 -*-
"""Booking = rezervacija ene dvorane za en časovni okvir."""
from odoo import _, api, fields, models
from odoo.exceptions import ValidationError, UserError


class L10nSiEventBooking(models.Model):
    _name = 'l10n_si.event.booking'
    _description = 'Slovenian Event Booking'
    _order = 'date_from DESC'

    name = fields.Char(compute='_compute_name', store=True)
    number = fields.Char(copy=False, readonly=True, default='/')
    event_id = fields.Many2one('l10n_si.event.event', required=True, ondelete='cascade')
    hall_id = fields.Many2one('l10n_si.event.hall', required=True, ondelete='restrict')

    # Časovni okvir (vključuje setup + teardown!)
    date_from = fields.Datetime(required=True, string='Od (vklj. priprava)')
    date_to = fields.Datetime(required=True, string='Do (vklj. razstavljanje)')
    event_start = fields.Datetime(string='Dejanski začetek dogodka')
    event_end = fields.Datetime(string='Dejanski konec dogodka')
    duration_hours = fields.Float(compute='_compute_duration', store=True, string='Skupne ure')

    # Cena
    pricing_type = fields.Selection(
        selection=[('hourly', 'Urno'),
                   ('half_day', 'Pol dneh'),
                   ('daily', 'Dnevno'),
                   ('package', 'V paketu')],
        default='daily',
        required=True,
    )
    unit_price = fields.Float(required=True, default=400.0)
    total_amount = fields.Monetary(compute='_compute_total', store=True, currency_field='currency_id')
    currency_id = fields.Many2one('res.currency', related='event_id.currency_id', store=True)

    # Status
    state = fields.Selection(related='event_id.state', store=True)

    notes = fields.Text()

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('number', '/') == '/':
                vals['number'] = self.env['ir.sequence'].next_by_code('l10n_si.event.booking') or '/'
        return super().create(vals_list)

    @api.depends('event_id.name', 'hall_id.name')
    def _compute_name(self):
        for b in self:
            ev = b.event_id.name or ''
            hall = b.hall_id.name or ''
            b.name = f'{ev} - {hall}'

    @api.depends('date_from', 'date_to')
    def _compute_duration(self):
        for b in self:
            if b.date_from and b.date_to:
                delta = b.date_to - b.date_from
                b.duration_hours = delta.total_seconds() / 3600.0
            else:
                b.duration_hours = 0.0

    @api.depends('pricing_type', 'unit_price', 'duration_hours', 'hall_id')
    def _compute_total(self):
        for b in self:
            if b.pricing_type == 'hourly':
                b.total_amount = b.duration_hours * b.unit_price
            elif b.pricing_type == 'half_day':
                b.total_amount = b.unit_price
            elif b.pricing_type == 'daily':
                days = max(b.duration_hours / 24.0, 1.0)
                b.total_amount = days * b.unit_price
            elif b.pricing_type == 'package':
                b.total_amount = 0.0  # Vključeno v paket na event nivoju
            else:
                b.total_amount = b.unit_price

    @api.onchange('hall_id', 'pricing_type')
    def _onchange_pricing(self):
        if self.hall_id:
            if self.pricing_type == 'hourly':
                self.unit_price = self.hall_id.hourly_rate
            elif self.pricing_type == 'half_day':
                self.unit_price = self.hall_id.half_day_rate
            elif self.pricing_type == 'daily':
                self.unit_price = self.hall_id.daily_rate

    @api.constrains('date_from', 'date_to', 'hall_id')
    def _check_availability(self):
        for b in self:
            if b.date_from and b.date_to and b.hall_id:
                if not b.hall_id.is_available(b.date_from, b.date_to, exclude_booking_id=b.id):
                    raise ValidationError(_(
                        'Dvorana %s ni prosta v izbranem času.', ) % b.hall_id.name)
