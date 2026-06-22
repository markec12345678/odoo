# -*- coding: utf-8 -*-
"""Rezervacija mize."""
from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class L10nSiRestaurantReservation(models.Model):
    _name = 'l10n_si.restaurant.reservation'
    _description = 'Slovenian Restaurant Table Reservation'
    _inherit = ['mail.thread']
    _order = 'reservation_date DESC'

    name = fields.Char(copy=False, readonly=True, default='/')
    partner_id = fields.Many2one('res.partner', string='Gost', required=True, tracking=True)
    table_id = fields.Many2one('l10n_si.restaurant.table', string='Miza', required=True, ondelete='restrict')

    reservation_date = fields.Datetime(required=True, default=fields.Datetime.now)
    duration_hours = fields.Float(default=2.0, required=True)
    end_datetime = fields.Datetime(compute='_compute_end', store=True)

    guests = fields.Integer(string='Število gostov', default=2, required=True)
    state = fields.Selection(
        selection=[('draft', 'Osnutek'),
                   ('confirmed', 'Potrjena'),
                   ('seated', 'Sedijo'),
                   ('finished', 'Končano'),
                   ('no_show', 'Ni prišel'),
                   ('cancelled', 'Preklicana')],
        default='draft',
        tracking=True,
    )

    phone = fields.Char(related='partner_id.phone')
    email = fields.Char(related='partner_id.email')
    notes = fields.Text(string='Posebne želje (alergije, ...)')
    company_id = fields.Many2one(
        'res.company', string='Company',
        default=lambda self: self.env.company, required=True,
    )

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', '/') == '/':
                vals['name'] = self.env['ir.sequence'].next_by_code('l10n_si.restaurant.reservation') or '/'
        return super().create(vals_list)

    @api.depends('reservation_date', 'duration_hours')
    def _compute_end(self):
        from datetime import timedelta
        for r in self:
            if r.reservation_date and r.duration_hours:
                r.end_datetime = r.reservation_date + timedelta(hours=r.duration_hours)
            else:
                r.end_datetime = False

    @api.constrains('guests', 'table_id')
    def _check_capacity(self):
        for r in self:
            if r.table_id and r.guests > r.table_id.capacity:
                raise ValidationError(_(
                    'Miza %(table)s sprejme največ %(cap)d gostov, rezervacija je za %(g)d.',
                    table=r.table_id.name, cap=r.table_id.capacity, g=r.guests,
                ))

    def action_confirm(self):
        for r in self:
            r.state = 'confirmed'
            r.table_id.state = 'reserved'

    def action_seat(self):
        for r in self:
            r.state = 'seated'
            r.table_id.state = 'occupied'

    def action_finish(self):
        for r in self:
            r.state = 'finished'
            r.table_id.state = 'cleaning'

    def action_cancel(self):
        for r in self:
            r.state = 'cancelled'
            if r.table_id.state == 'reserved':
                r.table_id.state = 'free'

    def action_no_show(self):
        self.write({'state': 'no_show'})
        for r in self:
            if r.table_id.state == 'reserved':
                r.table_id.state = 'free'
