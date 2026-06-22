# -*- coding: utf-8 -*-
"""Rate plan - cenovni načrt z pravili za dinamično določanje cene."""
from odoo import api, fields, models


class L10nSiRatePlan(models.Model):
    _name = 'l10n_si.rate.plan'
    _description = 'Slovenian Rate Plan'
    _order = 'sequence, name'

    name = fields.Char(required=True, translate=True)
    code = fields.Char(required=True, size=16)
    sequence = fields.Integer(default=10)
    active = fields.Boolean(default=True)
    company_id = fields.Many2one(
        'res.company', string='Company',
        default=lambda self: self.env.company, required=True,
    )

    # Soba/parcela na katero velja
    applies_to = fields.Selection(
        selection=[('hotel_room_type', 'Hotel - vrsta sobe'),
                   ('camping_parcel', 'Kamp - parcela')],
        required=True,
        default='hotel_room_type',
    )
    hotel_room_type_id = fields.Many2one('l10n_si.hotel.room.type')
    camping_parcel_id = fields.Many2one('l10n_si.camping.parcel')

    # Osnovna cena (BAR - Best Available Rate)
    base_price = fields.Float(required=True, default=80.0, string='Osnovna cena (BAR)')

    # Pravila za prilagoditev cene
    # 1. Sezonski faktorji
    winter_factor = fields.Float(default=0.7, string='Zima faktor')
    shoulder_factor = fields.Float(default=1.0, string='Prelivna faktor')
    high_season_factor = fields.Float(default=1.5, string='Visoka sezona')
    peak_factor = fields.Float(default=1.8, string='Vrhunec (prazniki)')

    # 2. Dan v tednu
    weekday_factor = fields.Float(default=1.0, string='Delavnik faktor')
    friday_factor = fields.Float(default=1.2, string='Petek')
    saturday_factor = fields.Float(default=1.3, string='Sobota')
    sunday_factor = fields.Float(default=0.9, string='Nedelja')

    # 3. Zasedenost (occupancy-based)
    occ_0_30_factor = fields.Float(default=0.85, string='Zasedenost 0-30% faktor')
    occ_31_60_factor = fields.Float(default=1.0, string='Zasedenost 31-60% faktor')
    occ_61_85_factor = fields.Float(default=1.15, string='Zasedenost 61-85% faktor')
    occ_86_100_factor = fields.Float(default=1.4, string='Zasedenost 86-100% faktor')

    # 4. Last-minute (čim bližje datumu, dražje)
    last_minute_days_threshold = fields.Integer(default=3, string='Last-minute prag (dnevi)')
    last_minute_factor = fields.Float(default=1.2, string='Last-minute faktor')

    # 5. Zgodnja rezervacija (early bird)
    early_bird_days_threshold = fields.Integer(default=60, string='Early-bird prag (dnevi)')
    early_bird_factor = fields.Float(default=0.9, string='Early-bird faktor')

    # 6. Dolžina bivanja (length of stay)
    los_7_plus_factor = fields.Float(default=0.92, string='7+ nočitev faktor')
    los_14_plus_factor = fields.Float(default=0.85, string='14+ nočitev faktor')

    # Omejitve
    min_los = fields.Integer(default=1, string='Min. nočitev')
    max_los = fields.Integer(default=30, string='Max. nočitev')
    closed_to_arrival = fields.Boolean(default=False, string='Zaprto za prihod')
    closed_to_departure = fields.Boolean(default=False, string='Zaprto za odhod')

    # CTAs/CTDs datumi (posebni datumi)
    cta_dates = fields.Text(string='CTA datumi (CSV)',
                              help='Datumi, ko je zaprto za prihod. Format: 2025-12-24,2025-12-31')

    description = fields.Text()
    currency_id = fields.Many2one(
        'res.currency', default=lambda self: self.env.company.currency_id, required=True,
    )

    _sql_constraints = [
        ('code_company_uniq', 'unique(code, company_id)', 'Code must be unique per company.'),
    ]

    def compute_rate(self, target_date, occupancy_percent=0, days_to_arrival=0, length_of_stay=1):
        """Izračunaj ceno za določen datum glede na vsa pravila.

        Args:
            target_date: datum za katerega računamo ceno
            occupancy_percent: trenutna zasedenost (%)
            days_to_arrival: koliko dni do prihoda
            length_of_stay: dolžina bivanja v nočitvah

        Returns:
            (cena EUR, seznam uporabljenih faktorjev)
        """
        self.ensure_one()
        factors = []
        rate = self.base_price

        # 1. Sezona (preko l10n_si_camping.season)
        season = self.env['l10n_si.camping.season'].get_season_for_date(target_date) if hasattr(self.env['l10n_si.camping.season'], 'get_season_for_date') else False
        if season:
            if season.code == 'low':
                rate *= self.winter_factor
                factors.append(f'Zima ({self.winter_factor}x)')
            elif season.code == 'shoulder':
                rate *= self.shoulder_factor
                factors.append(f'Prelivna ({self.shoulder_factor}x)')
            elif season.code == 'high':
                rate *= self.high_season_factor
                factors.append(f'Visoka ({self.high_season_factor}x)')
            elif season.code == 'peak':
                rate *= self.peak_factor
                factors.append(f'Vrhunec ({self.peak_factor}x)')

        # 2. Dan v tednu
        weekday = target_date.weekday()  # 0=Mon, 6=Sun
        if weekday == 4:  # Friday
            rate *= self.friday_factor
            factors.append(f'Petek ({self.friday_factor}x)')
        elif weekday == 5:  # Saturday
            rate *= self.saturday_factor
            factors.append(f'Sobota ({self.saturday_factor}x)')
        elif weekday == 6:  # Sunday
            rate *= self.sunday_factor
            factors.append(f'Nedelja ({self.sunday_factor}x)')
        else:
            rate *= self.weekday_factor

        # 3. Zasedenost
        if occupancy_percent <= 30:
            rate *= self.occ_0_30_factor
            factors.append(f'Zasedenost 0-30% ({self.occ_0_30_factor}x)')
        elif occupancy_percent <= 60:
            rate *= self.occ_31_60_factor
            factors.append(f'Zasedenost 31-60% ({self.occ_31_60_factor}x)')
        elif occupancy_percent <= 85:
            rate *= self.occ_61_85_factor
            factors.append(f'Zasedenost 61-85% ({self.occ_61_85_factor}x)')
        else:
            rate *= self.occ_86_100_factor
            factors.append(f'Zasedenost 86-100% ({self.occ_86_100_factor}x)')

        # 4. Last-minute
        if 0 <= days_to_arrival <= self.last_minute_days_threshold:
            rate *= self.last_minute_factor
            factors.append(f'Last-minute ({self.last_minute_factor}x)')

        # 5. Early-bird
        if days_to_arrival >= self.early_bird_days_threshold:
            rate *= self.early_bird_factor
            factors.append(f'Early-bird ({self.early_bird_factor}x)')

        # 6. Length of stay
        if length_of_stay >= 14:
            rate *= self.los_14_plus_factor
            factors.append(f'LOS 14+ ({self.los_14_plus_factor}x)')
        elif length_of_stay >= 7:
            rate *= self.los_7_plus_factor
            factors.append(f'LOS 7+ ({self.los_7_plus_factor}x)')

        return round(rate, 2), factors

    def get_rate_for_date(self, target_date):
        """Public method: get computed rate for a date with default occupancy 50%."""
        rate, factors = self.compute_rate(target_date, occupancy_percent=50)
        return rate
