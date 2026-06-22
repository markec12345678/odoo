# -*- coding: utf-8 -*-
"""Hotel reservation - guest booking for a room + dates."""
from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class HotelReservation(models.Model):
    """One booking: guest + room + check-in/check-out dates.

    Lifecycle:
        draft → confirmed → checked_in → checked_out → cancelled
    """
    _name = 'l10n_si.hotel.reservation'
    _description = 'Slovenian Hotel Reservation'
    _inherit = ['mail.thread']
    _order = 'check_in DESC'

    name = fields.Char(copy=False, readonly=True, default='/')
    partner_id = fields.Many2one('res.partner', string='Gost', required=True, tracking=True)
    company_id = fields.Many2one(
        'res.company', string='Company',
        default=lambda self: self.env.company, required=True,
    )

    # Room + dates
    room_id = fields.Many2one('l10n_si.hotel.room', required=True, ondelete='restrict')
    room_type_id = fields.Many2one(related='room_id.room_type_id', store=True)
    check_in = fields.Datetime(required=True, default=fields.Datetime.now)
    check_out = fields.Datetime(required=True)

    # Pricing
    daily_rate = fields.Float(required=True, default=80.0)
    nights = fields.Integer(compute='_compute_nights', store=True)
    total_amount = fields.Monetary(compute='_compute_total', store=True, currency_field='currency_id')
    currency_id = fields.Many2one(
        'res.currency', related='company_id.currency_id', store=True, readonly=True,
    )

    # State
    state = fields.Selection(
        selection=[('draft', 'Osnutek'),
                   ('confirmed', 'Potrjena'),
                   ('checked_in', 'Prijava'),
                   ('checked_out', 'Odjava'),
                   ('no_show', 'Ni prišel'),
                   ('cancelled', 'Preklicana')],
        default='draft',
        tracking=True,
    )

    # Guest details
    adults = fields.Integer(default=2)
    children = fields.Integer(default=0)
    special_requests = fields.Text()
    source = fields.Selection(
        selection=[('direct', 'Direktno'),
                   ('phone', 'Telefon'),
                   ('email', 'E-pošta'),
                   ('website', 'Spletna stran'),
                   ('booking_com', 'Booking.com'),
                   ('airbnb', 'Airbnb'),
                   ('expedia', 'Expedia'),
                   ('agency', 'Agencija'),
                   ('other', 'Drugo')],
        default='direct',
    )

    # Folio link
    folio_id = fields.Many2one('l10n_si.hotel.folio', string='Folio')

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', '/') == '/':
                vals['name'] = self.env['ir.sequence'].next_by_code('l10n_si.hotel.reservation') or '/'
        return super().create(vals_list)

    @api.depends('check_in', 'check_out')
    def _compute_nights(self):
        for res in self:
            if res.check_in and res.check_out:
                delta = res.check_out - res.check_in
                res.nights = max(delta.days, 0)
            else:
                res.nights = 0

    @api.depends('nights', 'daily_rate')
    def _compute_total(self):
        for res in self:
            res.total_amount = res.nights * res.daily_rate

    @api.onchange('room_id')
    def _onchange_room_id(self):
        if self.room_id and self.room_id.room_type_id:
            self.daily_rate = self.room_id.room_type_id.list_price

    @api.constrains('check_in', 'check_out')
    def _check_dates(self):
        for res in self:
            if res.check_in and res.check_out and res.check_out <= res.check_in:
                raise ValidationError(_('Check-out must be after check-in.'))

    def action_confirm(self):
        for res in self:
            if not res.room_id.is_available(res.check_in.date(), res.check_out.date()):
                raise ValidationError(_(
                    'Room %s is not available for the selected dates.',
                ) % res.room_id.number)
            res.state = 'confirmed'
            res.room_id.state = 'reserved'

    def action_check_in(self):
        """Check-in: opens/creates a folio for this reservation."""
        Folio = self.env['l10n_si.hotel.folio']
        for res in self:
            if not res.folio_id:
                folio = Folio.create({
                    'partner_id': res.partner_id.id,
                    'check_in': res.check_in,
                    'check_out': res.check_out,
                    'adults': res.adults,
                    'children': res.children,
                    'room_ids': [(6, 0, [res.room_id.id])],
                })
                res.folio_id = folio.id
            res.folio_id.action_open()
            res.state = 'checked_in'

    def action_check_out(self):
        """Check-out: close folio and offer to create invoice."""
        for res in self:
            if res.folio_id:
                res.folio_id.action_close()
            res.state = 'checked_out'

    def action_cancel(self):
        for res in self:
            if res.folio_id and res.folio_id.state == 'open':
                raise ValidationError(_(
                    'Cannot cancel a reservation with an open folio. Check-out first.',
                ))
            res.state = 'cancelled'
            if res.room_id.state == 'reserved':
                res.room_id.state = 'available'

    def action_no_show(self):
        """Mark guest as not arrived - room becomes available again."""
        for res in res:
            res.state = 'no_show'
            if res.room_id.state == 'reserved':
                res.room_id.state = 'available'
