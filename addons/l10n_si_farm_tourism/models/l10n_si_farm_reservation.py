# -*- coding: utf-8 -*-
"""Rezervacija sobe na kmetiji."""
from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class L10nSiFarmReservation(models.Model):
    _name = 'l10n_si.farm.reservation'
    _description = 'Slovenian Farm Reservation'
    _inherit = ['mail.thread']
    _order = 'check_in DESC'

    name = fields.Char(copy=False, readonly=True, default='/')
    partner_id = fields.Many2one('res.partner', string='Gost', required=True, tracking=True)
    room_id = fields.Many2one('l10n_si.farm.room', required=True, ondelete='restrict')

    check_in = fields.Datetime(required=True, default=fields.Datetime.now)
    check_out = fields.Datetime(required=True)
    nights = fields.Integer(compute='_compute_nights', store=True)

    # Guests
    adults = fields.Integer(default=2, required=True)
    children = fields.Integer(default=0)
    breakfast = fields.Boolean(default=True, string='Zajtrk vključen')
    dinner = fields.Boolean(default=False, string='Večerja na kmetiji')
    dinner_price = fields.Float(string='Cena večerje (EUR/oseba)', default=18.0)

    # Activity bookings
    farm_activities = fields.Many2many(
        'l10n_si.farm.activity', string='Kmečke aktivnosti',
        help='Mladi/pridelava/dejavnosti na kmetiji.',
    )

    # Pricing
    daily_rate = fields.Float(compute='_compute_rate', store=True, readonly=False)
    total_amount = fields.Monetary(compute='_compute_total', store=True, currency_field='currency_id')
    currency_id = fields.Many2one('res.currency', related='company_id.currency_id', store=True)

    state = fields.Selection(
        selection=[('draft', 'Osnutek'),
                   ('confirmed', 'Potrjena'),
                   ('checked_in', 'Prijavljeni'),
                   ('checked_out', 'Odjavljeni'),
                   ('cancelled', 'Preklicana')],
        default='draft',
        tracking=True,
    )

    notes = fields.Text(string='Posebne želje (alergije, dieta)')
    move_id = fields.Many2one('account.move', string='Račun', readonly=True, copy=False)
    company_id = fields.Many2one(
        'res.company', string='Company',
        default=lambda self: self.env.company, required=True,
    )

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', '/') == '/':
                vals['name'] = self.env['ir.sequence'].next_by_code('l10n_si.farm.reservation') or '/'
        return super().create(vals_list)

    @api.depends('check_in', 'check_out')
    def _compute_nights(self):
        for r in self:
            if r.check_in and r.check_out:
                r.nights = max((r.check_out - r.check_in).days, 0)
            else:
                r.nights = 0

    @api.depends('room_id', 'breakfast')
    def _compute_rate(self):
        for r in self:
            if not r.room_id:
                r.daily_rate = 0
                continue
            rate = r.room_id.price_per_night
            if r.breakfast and not r.room_id.breakfast_included:
                rate += r.room_id.breakfast_price * (r.adults + r.children)
            r.daily_rate = rate

    @api.depends('nights', 'daily_rate', 'adults', 'children', 'dinner', 'dinner_price')
    def _compute_total(self):
        for r in self:
            total = r.nights * r.daily_rate
            if r.dinner:
                total += r.nights * (r.adults + r.children) * r.dinner_price
            r.total_amount = total

    @api.constrains('check_in', 'check_out')
    def _check_dates(self):
        for r in self:
            if r.check_in and r.check_out and r.check_out <= r.check_in:
                raise ValidationError(_('Check-out must be after check-in.'))

    def action_confirm(self):
        for r in self:
            if not r.room_id.is_available(r.check_in.date(), r.check_out.date()):
                raise ValidationError(_('Room %s not available.') % r.room_id.name)
            r.state = 'confirmed'
            r.room_id.state = 'reserved'

    def action_check_in(self):
        for r in self:
            r.state = 'checked_in'
            r.room_id.state = 'occupied'

    def action_check_out(self):
        """Create invoice + trigger FURS."""
        Invoice = self.env['account.move']
        for r in self:
            if not r.move_id:
                lines = [(0, 0, {
                    'name': f'Soba {r.room_id.name} - {r.nights} nočitev',
                    'quantity': r.nights,
                    'price_unit': r.room_id.price_per_night,
                })]
                if r.breakfast and not r.room_id.breakfast_included:
                    lines.append((0, 0, {
                        'name': 'Zajtrk',
                        'quantity': r.nights * (r.adults + r.children),
                        'price_unit': r.room_id.breakfast_price,
                    }))
                if r.dinner:
                    lines.append((0, 0, {
                        'name': 'Večerja na kmetiji',
                        'quantity': r.nights * (r.adults + r.children),
                        'price_unit': r.dinner_price,
                    }))
                move = Invoice.create({
                    'move_type': 'out_invoice',
                    'partner_id': r.partner_id.id,
                    'invoice_date': fields.Date.today(),
                    'company_id': r.company_id.id,
                    'invoice_line_ids': lines,
                })
                move.action_post()  # FURS via l10n_si_fiscal
                r.move_id = move.id
            r.state = 'checked_out'
            r.room_id.state = 'available'

    def action_cancel(self):
        for r in self:
            r.state = 'cancelled'
            if r.room_id.state == 'reserved':
                r.room_id.state = 'available'


class L10nSiFarmActivity(models.Model):
    _name = 'l10n_si.farm.activity'
    _description = 'Slovenian Farm Activity'

    name = fields.Char(required=True, translate=True)
    description = fields.Text()
    duration_hours = fields.Float(default=2.0)
    price_per_person = fields.Float(default=15.0)
    max_participants = fields.Integer(default=10)
    active = fields.Boolean(default=True)
    season = fields.Selection(
        selection=[('spring', 'Pomlad'),
                   ('summer', 'Poletje'),
                   ('autumn', 'Jesen'),
                   ('winter', 'Zima'),
                   ('all_year', 'Vse leto')],
        default='all_year',
    )
