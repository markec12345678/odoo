# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from datetime import datetime, timedelta

from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestHotelWorkflow(TransactionCase):
    """End-to-end lifecycle of a hotel reservation.

    draft → confirmed → checked_in → checked_out
                     ↘ no_show
    """

    def setUp(self):
        super().setUp()
        self.room_type = self.env['l10n_si.hotel.room.type'].create({
            'name': 'Standard',
            'code': 'STD',
            'list_price': 80.0,
        })
        self.room = self.env['l10n_si.hotel.room'].create({
            'number': '101',
            'floor': 1,
            'room_type_id': self.room_type.id,
        })
        self.partner = self.env['res.partner'].create({
            'name': 'Janez Novak',
        })
        self.check_in = datetime(2025, 3, 10, 14, 0, 0)
        self.check_out = self.check_in + timedelta(days=3)
        self.reservation = self.env['l10n_si.hotel.reservation'].create({
            'partner_id': self.partner.id,
            'room_id': self.room.id,
            'check_in': self.check_in,
            'check_out': self.check_out,
            'adults': 2,
            'children': 0,
            'daily_rate': 80.0,
        })

    def test_default_state_is_draft(self):
        """A new reservation starts in the 'draft' state."""
        self.assertEqual(self.reservation.state, 'draft')

    def test_nights_computed(self):
        """nights = (check_out - check_in).days."""
        self.assertEqual(self.reservation.nights, 3)

    def test_action_confirm_sets_confirmed_and_reserves_room(self):
        """Confirming a reservation marks it 'confirmed' and the room 'reserved'."""
        self.reservation.action_confirm()
        self.assertEqual(self.reservation.state, 'confirmed')
        self.assertEqual(self.room.state, 'reserved')

    def test_action_check_in_creates_folio_and_occupies_room(self):
        """Check-in creates a folio, sets state to checked_in and room to occupied."""
        self.reservation.action_confirm()
        self.reservation.action_check_in()
        self.assertEqual(self.reservation.state, 'checked_in')
        self.assertTrue(self.reservation.folio_id,
                        'Check-in must create/link a folio.')
        self.assertEqual(self.room.state, 'occupied')
        self.assertEqual(self.reservation.folio_id.state, 'open')

    def test_action_check_out_sets_checked_out_and_room_cleaning(self):
        """Check-out closes the folio, sets state to checked_out and room to cleaning."""
        self.reservation.action_confirm()
        self.reservation.action_check_in()
        self.reservation.action_check_out()
        self.assertEqual(self.reservation.state, 'checked_out')
        self.assertEqual(self.room.state, 'cleaning')
        self.assertEqual(self.reservation.folio_id.state, 'closed')

    def test_action_no_show_releases_room(self):
        """No-show marks the reservation and frees the reserved room.

        Regression test for the bug where ``action_no_show`` used
        ``for res in res:`` instead of ``for res in self:``, which raised
        a NameError at runtime.
        """
        self.reservation.action_confirm()
        self.assertEqual(self.room.state, 'reserved')
        # Must not raise — the bug fix changed ``for res in res`` to ``for res in self``.
        self.reservation.action_no_show()
        self.assertEqual(self.reservation.state, 'no_show')
        self.assertEqual(self.room.state, 'available')
