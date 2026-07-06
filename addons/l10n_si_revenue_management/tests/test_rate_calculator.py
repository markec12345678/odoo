# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from datetime import date

from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestRateCalculator(TransactionCase):
    """Unit tests for ``l10n_si.rate.plan.compute_rate``.

    The compute_rate method multiplies the base price by a chain of factors:
        season × weekday × occupancy × last-minute × early-bird × LOS

    Each test isolates one or two factors by choosing a date / occupancy /
    lead time / LOS that leaves the other factors at their neutral value.
    """

    def setUp(self):
        super().setUp()
        self.rate_plan = self.env['l10n_si.rate.plan'].create({
            'name': 'Test BAR',
            'code': 'BAR-T',
            'applies_to': 'hotel_room_type',
            'base_price': 100.0,
            # Season factors — not exercised (no l10n_si.camping.season rows in
            # the test DB, so get_season_for_date returns False).
            'winter_factor': 0.7,
            'shoulder_factor': 1.0,
            'high_season_factor': 1.5,
            'peak_factor': 1.8,
            # Weekday factors
            'weekday_factor': 1.0,
            'friday_factor': 1.2,
            'saturday_factor': 1.3,
            'sunday_factor': 0.9,
            # Occupancy factors
            'occ_0_30_factor': 0.85,
            'occ_31_60_factor': 1.0,
            'occ_61_85_factor': 1.15,
            'occ_86_100_factor': 1.4,
            # Lead time
            'last_minute_days_threshold': 3,
            'last_minute_factor': 1.2,
            'early_bird_days_threshold': 60,
            'early_bird_factor': 0.9,
            # Length of stay
            'los_7_plus_factor': 0.92,
            'los_14_plus_factor': 0.85,
        })
        # 2025-01-06 is a Monday (weekday 0) → weekday_factor 1.0 (neutral).
        self.monday = date(2025, 1, 6)
        # 2025-01-03 is a Friday (weekday 4).
        self.friday = date(2025, 1, 3)
        # 2025-01-04 is a Saturday (weekday 5).
        self.saturday = date(2025, 1, 4)

    # ------------------------------------------------------------------
    # Single-factor cases
    # ------------------------------------------------------------------

    def test_base_rate_with_zero_occupancy(self):
        """0% occupancy on a weekday: 100 × 1.0 × 0.85 = 85."""
        rate, factors = self.rate_plan.compute_rate(
            self.monday, occupancy_percent=0, days_to_arrival=30, length_of_stay=1,
        )
        self.assertEqual(rate, 85.0)
        self.assertIn('Zasedenost 0-30%', ' '.join(factors))

    def test_friday_factor(self):
        """Friday multiplier 1.2x on top of the 0-30% occupancy band:
        100 × 1.2 × 0.85 = 102.
        """
        rate, factors = self.rate_plan.compute_rate(
            self.friday, occupancy_percent=0, days_to_arrival=30, length_of_stay=1,
        )
        self.assertEqual(rate, 102.0)
        self.assertIn('Petek', ' '.join(factors))

    def test_saturday_factor(self):
        """Saturday multiplier 1.3x: 100 × 1.3 × 0.85 = 110.5."""
        rate, factors = self.rate_plan.compute_rate(
            self.saturday, occupancy_percent=0, days_to_arrival=30, length_of_stay=1,
        )
        self.assertEqual(rate, 110.5)
        self.assertIn('Sobota', ' '.join(factors))

    def test_high_occupancy_factor(self):
        """90% occupancy falls in the 86-100% band (1.4x):
        100 × 1.0 (weekday) × 1.4 = 140.
        """
        rate, factors = self.rate_plan.compute_rate(
            self.monday, occupancy_percent=90, days_to_arrival=30, length_of_stay=1,
        )
        self.assertEqual(rate, 140.0)
        self.assertIn('Zasedenost 86-100%', ' '.join(factors))

    def test_last_minute_factor(self):
        """days_to_arrival=3 (≤ threshold) triggers last-minute 1.2x:
        100 × 1.0 × 0.85 × 1.2 = 102.
        """
        rate, factors = self.rate_plan.compute_rate(
            self.monday, occupancy_percent=0, days_to_arrival=3, length_of_stay=1,
        )
        self.assertEqual(rate, 102.0)
        self.assertIn('Last-minute', ' '.join(factors))

    def test_early_bird_factor(self):
        """days_to_arrival=60 (≥ threshold) triggers early-bird 0.9x:
        100 × 1.0 × 0.85 × 0.9 = 76.5.
        """
        rate, factors = self.rate_plan.compute_rate(
            self.monday, occupancy_percent=0, days_to_arrival=60, length_of_stay=1,
        )
        self.assertEqual(rate, 76.5)
        self.assertIn('Early-bird', ' '.join(factors))

    def test_los_7_plus_factor(self):
        """LOS 7 triggers the 7+ factor 0.92x:
        100 × 1.0 × 0.85 × 0.92 = 78.2.
        """
        rate, factors = self.rate_plan.compute_rate(
            self.monday, occupancy_percent=0, days_to_arrival=30, length_of_stay=7,
        )
        self.assertEqual(rate, 78.2)
        self.assertIn('LOS 7+', ' '.join(factors))

    # ------------------------------------------------------------------
    # Combined factors
    # ------------------------------------------------------------------

    def test_multiple_factors_combined(self):
        """Saturday (1.3) + 90% occ (1.4) + last-minute (1.2):
        100 × 1.3 × 1.4 × 1.2 = 218.4.
        """
        rate, factors = self.rate_plan.compute_rate(
            self.saturday, occupancy_percent=90, days_to_arrival=3, length_of_stay=1,
        )
        self.assertEqual(rate, 218.4)
        factor_str = ' '.join(factors)
        self.assertIn('Sobota', factor_str)
        self.assertIn('Zasedenost 86-100%', factor_str)
        self.assertIn('Last-minute', factor_str)
