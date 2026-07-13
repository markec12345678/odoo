# -*- coding: utf-8 -*-
"""Kamp rezervacija."""
from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class L10nSiCampingReservation(models.Model):
    _name = 'l10n_si.camping.reservation'
    _description = 'Slovenian Camping Reservation'
    _inherit = ['mail.thread']
    _order = 'check_in DESC'

    name = fields.Char(copy=False, readonly=True, default='/')
    partner_id = fields.Many2one('res.partner', string='Gost', required=True, tracking=True)
    parcel_id = fields.Many2one('l10n_si.camping.parcel', required=True, ondelete='restrict')

    check_in = fields.Datetime(required=True, default=fields.Datetime.now)
    check_out = fields.Datetime(required=True)
    nights = fields.Integer(compute='_compute_nights', store=True)

    # People
    adults = fields.Integer(default=2, required=True)
    children = fields.Integer(default=0)
    vehicles = fields.Integer(default=1, help='Število avtodomov/prikolic')
    tents = fields.Integer(default=1)
    pets = fields.Integer(default=0)

    # Pricing
    daily_rate = fields.Float(compute='_compute_rate', store=True, readonly=False)
    total_amount = fields.Monetary(compute='_compute_total', store=True, currency_field='currency_id')
    currency_id = fields.Many2one('res.currency', related='company_id.currency_id', store=True)

    # State
    state = fields.Selection(
        selection=[('draft', 'Osnutek'),
                   ('confirmed', 'Potrjena'),
                   ('checked_in', 'Prijavljeni'),
                   ('checked_out', 'Odjavljeni'),
                   ('no_show', 'Ni prišel'),
                   ('cancelled', 'Preklicana')],
        default='draft',
        tracking=True,
    )

    # Source
    source = fields.Selection(
        selection=[('direct', 'Direktno'),
                   ('phone', 'Telefon'),
                   ('website', 'Spletna stran'),
                   ('booking_com', 'Booking.com'),
                   ('airbnb', 'Airbnb'),
                   ('camping_com', 'Camping.com'),
                   ('agency', 'Agencija')],
        default='direct',
    )

    # Notes
    notes = fields.Text(string='Opombe (alergije, posebne želje)')
    move_id = fields.Many2one('account.move', string='Račun', readonly=True, copy=False)
    company_id = fields.Many2one(
        'res.company', string='Company',
        default=lambda self: self.env.company, required=True,
    )

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', '/') == '/':
                vals['name'] = self.env['ir.sequence'].next_by_code('l10n_si.camping.reservation') or '/'
        return super().create(vals_list)

    @api.depends('check_in', 'check_out')
    def _compute_nights(self):
        for res in self:
            if res.check_in and res.check_out:
                delta = res.check_out - res.check_in
                res.nights = max(delta.days, 0)
            else:
                res.nights = 0

    @api.depends('parcel_id', 'check_in', 'adults', 'nights')
    def _compute_rate(self):
        """Daily rate = base_price × season_multiplier + extra_person_price × (adults - 1)."""
        for res in self:
            if not res.parcel_id or not res.check_in:
                res.daily_rate = 0
                continue
            season = self.env['l10n_si.camping.season'].get_season_for_date(res.check_in.date())
            multiplier = season.multiplier if season else 1.0
            base = res.parcel_id.base_price * multiplier
            extra = res.parcel_id.extra_person_price * max(res.adults - 1, 0)
            electricity = res.parcel_id.electricity_price if res.parcel_id.has_electricity else 0
            res.daily_rate = base + extra + electricity

    @api.depends('nights', 'daily_rate', 'parcel_id.long_stay_discount_days', 'parcel_id.long_stay_discount_percent')
    def _compute_total(self):
        for res in self:
            base_total = res.nights * res.daily_rate
            # Apply long-stay discount
            if (res.nights >= res.parcel_id.long_stay_discount_days
                    and res.parcel_id.long_stay_discount_percent > 0):
                discount = base_total * (res.parcel_id.long_stay_discount_percent / 100)
                res.total_amount = base_total - discount
            else:
                res.total_amount = base_total

    @api.constrains('check_in', 'check_out')
    def _check_dates(self):
        for r in self:
            if r.check_in and r.check_out and r.check_out <= r.check_in:
                raise ValidationError(_('Check-out must be after check-in.'))

    def action_confirm(self):
        for res in self:
            if not res.parcel_id.is_available(res.check_in.date(), res.check_out.date()):
                raise ValidationError(_('Parcel %s not available.') % res.parcel_id.name)
            res.state = 'confirmed'
            res.parcel_id.state = 'reserved'

    def action_check_in(self):
        for res in self:
            res.state = 'checked_in'
            res.parcel_id.state = 'occupied'

    def action_check_out(self):
        """Check-out: create invoice + trigger FURS."""
        Invoice = self.env['account.move']
        for res in self:
            if not res.move_id:
                lines = [(0, 0, {
                    'name': f'Kamp {res.parcel_id.name} - {res.nights} nočitev',
                    'quantity': res.nights,
                    'price_unit': res.daily_rate,
                })]
                # Add tourist tax line (placeholder - integrated with l10n_si_tourist_tax)
                # TODO: add tourist tax if l10n_si_tourist_tax is installed
                move = Invoice.create({
                    'move_type': 'out_invoice',
                    'partner_id': res.partner_id.id,
                    'invoice_date': fields.Date.today(),
                    'company_id': res.company_id.id,
                    'invoice_line_ids': lines,
                })
                move.action_post()  # FURS via l10n_si_fiscal
                res.move_id = move.id
            res.state = 'checked_out'
            res.parcel_id.state = 'available'

    def action_cancel(self):
        for res in self:
            res.state = 'cancelled'
            if res.parcel_id.state == 'reserved':
                res.parcel_id.state = 'available'

    def action_no_show(self):
        self.write({'state': 'no_show'})
        for res in self:
            if res.parcel_id.state == 'reserved':
                res.parcel_id.state = 'available'
