# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from datetime import datetime, timedelta

from odoo.exceptions import ValidationError
from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestHotelEdgeCases(TransactionCase):
    """Edge cases and constraint enforcement for the hotel module."""

    def setUp(self):
        super().setUp()
        self.room_type = self.env['l10n_si.hotel.room.type'].create({
            'name': 'Deluxe',
            'code': 'DLX',
            'list_price': 120.0,
        })
        self.room = self.env['l10n_si.hotel.room'].create({
            'number': '201',
            'floor': 2,
            'room_type_id': self.room_type.id,
        })
        self.partner = self.env['res.partner'].create({
            'name': 'Ana Kovač',
        })

    # ------------------------------------------------------------------
    # Nights computation
    # ------------------------------------------------------------------

    def test_same_day_check_in_out_is_zero_nights(self):
        """A stay of a few hours on the same calendar day = 0 nights.

        ``nights`` is computed from ``delta.days``, which is 0 when the
        checkout is later the same day.
        """
        check_in = datetime(2025, 4, 1, 14, 0, 0)
        check_out = datetime(2025, 4, 1, 20, 0, 0)  # same day, 6h later
        reservation = self.env['l10n_si.hotel.reservation'].create({
            'partner_id': self.partner.id,
            'room_id': self.room.id,
            'check_in': check_in,
            'check_out': check_out,
            'daily_rate': 100.0,
        })
        self.assertEqual(reservation.nights, 0)

    def test_negative_nights_raises_validation_error(self):
        """Check-out before check-in is rejected by the ``_check_dates`` constraint."""
        check_in = datetime(2025, 4, 2, 14, 0, 0)
        check_out = datetime(2025, 4, 1, 14, 0, 0)  # before check-in
        with self.assertRaises(ValidationError):
            self.env['l10n_si.hotel.reservation'].create({
                'partner_id': self.partner.id,
                'room_id': self.room.id,
                'check_in': check_in,
                'check_out': check_out,
                'daily_rate': 100.0,
            })

    # ------------------------------------------------------------------
    # Room constraints
    # ------------------------------------------------------------------

    def test_room_number_uniqueness_per_company(self):
        """Two rooms with the same number in the same company violate the
        ``number_company_uniq`` SQL constraint.
        """
        with self.assertRaises(Exception):
            self.env['l10n_si.hotel.room'].create({
                'number': '201',  # same as setUp room
                'floor': 3,
                'room_type_id': self.room_type.id,
            })

    # ------------------------------------------------------------------
    # Folio inheritance from reservation
    # ------------------------------------------------------------------

    def test_folio_inherits_adults_and_children(self):
        """On check-in, the folio inherits adults/children from the reservation."""
        reservation = self.env['l10n_si.hotel.reservation'].create({
            'partner_id': self.partner.id,
            'room_id': self.room.id,
            'check_in': datetime(2025, 5, 1, 14, 0, 0),
            'check_out': datetime(2025, 5, 1, 14, 0, 0) + timedelta(days=2),
            'adults': 3,
            'children': 2,
            'daily_rate': 120.0,
        })
        reservation.action_confirm()
        reservation.action_check_in()
        folio = reservation.folio_id
        self.assertTrue(folio)
        self.assertEqual(folio.adults, 3)
        self.assertEqual(folio.children, 2)
