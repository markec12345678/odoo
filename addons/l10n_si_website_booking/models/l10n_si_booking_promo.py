# -*- coding: utf-8 -*-
"""Promo codes for online booking."""
from odoo import api, fields, models


class L10nSiBookingPromo(models.Model):
    _name = 'l10n_si.booking.promo'
    _description = 'Slovenian Booking Promo Code'
    _order = 'valid_from DESC'

    name = fields.Char(required=True, translate=True)
    code = fields.Char(required=True, size=32, help='npr. EARLYBIRD20, SUMMER10')
    active = fields.Boolean(default=True)
    company_id = fields.Many2one(
        'res.company', string='Company',
        default=lambda self: self.env.company, required=True,
    )

    # Discount
    discount_type = fields.Selection(
        selection=[('percent', 'Procent'),
                   ('fixed', 'Fiksni znesek'),
                   ('free_night', 'Brezplačna nočitev'),
                   ('upgrade', 'Brezplačni upgrade')],
        default='percent',
        required=True,
    )
    discount_value = fields.Float(default=10.0, string='Vrednost popusta',
                                    help='Procent ali EUR glede na tip.')
    min_nights = fields.Integer(default=1, string='Min. nočitev')
    max_uses = fields.Integer(default=100, string='Max uporab')
    uses_count = fields.Integer(default=0, string='Uporabljeno')
    uses_remaining = fields.Integer(compute='_compute_uses', store=False)

    # Validity
    valid_from = fields.Date(required=True, default=fields.Date.today)
    valid_to = fields.Date(required=True)
    valid_room_type_ids = fields.Many2many('l10n_si.hotel.room.type',
                                             string='Veljavno za vrste sob (prazno = vse)')

    # Early bird
    min_days_before_arrival = fields.Integer(default=0, string='Min dni pred prihodom')
    max_days_before_arrival = fields.Integer(default=0, string='Max dni pred prihodom (0 = neomejeno)')

    description = fields.Text()
    usage_history_ids = fields.One2many('l10n_si.booking.promo.usage', 'promo_id', string='Zgodovina uporabe')

    _sql_constraints = [
        ('code_company_uniq', 'unique(code, company_id)', 'Promo code must be unique per company.'),
    ]

    def _compute_uses(self):
        for p in self:
            p.uses_remaining = p.max_uses - p.uses_count

    def is_valid(self, check_in, check_out, room_type_id=False):
        """Preveri, ali je promo koda veljavna za dane datume."""
        self.ensure_one()
        today = fields.Date.today()
        if not self.active:
            return False, 'Koda ni več aktivna.'
        if today < self.valid_from or today > self.valid_to:
            return False, 'Koda ni veljavna v tem obdobju.'
        if self.uses_count >= self.max_uses:
            return False, 'Koda je bila že uporabljena največkrat.'
        nights = (check_out - check_in).days if check_in and check_out else 0
        if nights < self.min_nights:
            return False, f'Potrebne so vsaj {self.min_nights} nočitve.'
        if self.valid_room_type_ids and room_type_id:
            if room_type_id not in self.valid_room_type_ids.ids:
                return False, 'Koda ne velja za to vrsto sobe.'
        days_before = (check_in - today).days
        if self.min_days_before_arrival and days_before < self.min_days_before_arrival:
            return False, f'Rezervirati morate vsaj {self.min_days_before_arrival} dni pred prihodom.'
        if self.max_days_before_arrival and days_before > self.max_days_before_arrival:
            return False, f'Rezervirati morate največ {self.max_days_before_arrival} dni pred prihodom.'
        return True, 'Veljavna.'

    def apply_discount(self, base_amount):
        """Izračunaj popust za dani znesek."""
        self.ensure_one()
        if self.discount_type == 'percent':
            return base_amount * (self.discount_value / 100.0)
        elif self.discount_type == 'fixed':
            return min(self.discount_value, base_amount)
        elif self.discount_type == 'free_night':
            # V produkciji: izračunaj ceno ene noči
            return 0.0
        return 0.0


class L10nSiBookingPromoUsage(models.Model):
    _name = 'l10n_si.booking.promo.usage'
    _description = 'Slovenian Booking Promo Usage'
    _order = 'create_date DESC'

    promo_id = fields.Many2one('l10n_si.booking.promo', required=True, ondelete='cascade')
    partner_id = fields.Many2one('res.partner', string='Gost')
    reservation_id = fields.Many2one('l10n_si.hotel.reservation', string='Rezervacija')
    discount_amount = fields.Float()
    create_date = fields.Datetime(default=fields.Datetime.now, readonly=True)
