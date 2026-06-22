# -*- coding: utf-8 -*-
"""Individual guest reservation within a block."""
from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class L10nSiEventAccommodationReservation(models.Model):
    _name = 'l10n_si.event.accommodation.reservation'
    _description = 'Slovenian Event Accommodation Guest Reservation'
    _inherit = ['mail.thread']
    _order = 'create_date DESC'

    name = fields.Char(copy=False, readonly=True, default='/')
    block_id = fields.Many2one('l10n_si.event.accommodation.block', required=True, ondelete='cascade')
    event_id = fields.Many2one(related='block_id.event_id', store=True)
    partner_id = fields.Many2one('res.partner', string='Gost', required=True)
    company_id = fields.Many2one('res.company', related='block_id.company_id', store=True)

    # Room
    room_id = fields.Many2one('l10n_si.hotel.room', required=True, ondelete='restrict')
    room_type_id = fields.Many2one(related='block_id.room_type_id', store=True)

    # Dates
    check_in = fields.Date(required=True, default=fields.Date.today)
    check_out = fields.Date(required=True)
    nights = fields.Integer(compute='_compute_nights', store=True)

    # Pricing
    daily_rate = fields.Float(related='block_id.special_rate', store=False)
    total_amount = fields.Monetary(compute='_compute_total', store=True, currency_field='currency_id')
    currency_id = fields.Many2one('res.currency', related='company_id.currency_id', store=True)

    # Status
    state = fields.Selection(
        selection=[('draft', 'Osnutek'),
                   ('confirmed', 'Potrjena'),
                   ('checked_in', 'Prijava'),
                   ('checked_out', 'Odjava'),
                   ('cancelled', 'Preklicana')],
        default='draft',
        tracking=True,
    )

    special_requests = fields.Text()

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', '/') == '/':
                vals['name'] = self.env['ir.sequence'].next_by_code('l10n_si.event.accommodation.reservation') or '/'
        return super().create(vals_list)

    @api.depends('check_in', 'check_out')
    def _compute_nights(self):
        for r in self:
            if r.check_in and r.check_out:
                r.nights = max((r.check_out - r.check_in).days, 0)
            else:
                r.nights = 0

    @api.depends('nights', 'daily_rate')
    def _compute_total(self):
        for r in self:
            r.total_amount = r.nights * r.daily_rate

    @api.constrains('block_id', 'room_id')
    def _check_room_in_block(self):
        for r in self:
            if r.room_id and r.block_id and r.room_id not in r.block_id.room_ids:
                raise ValidationError(_('Soba %s ni v bloku.') % r.room_id.name)

    def action_confirm(self):
        self.write({'state': 'confirmed'})

    def action_check_in(self):
        self.write({'state': 'checked_in'})

    def action_check_out(self):
        self.write({'state': 'checked_out'})

    def action_cancel(self):
        self.write({'state': 'cancelled'})
