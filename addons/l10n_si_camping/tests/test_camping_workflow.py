# -*- coding: utf-8 -*-
"""Tests for l10n_si_camping — parcel management and reservation lifecycle."""
from datetime import datetime, timedelta

from odoo.exceptions import ValidationError
from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestCampingParcel(TransactionCase):

    def setUp(self):
        super().setUp()
        self.Parcel = self.env['l10n_si.camping.parcel']
        self.parcel = self.Parcel.create({
            'number': 'A01',
            'zone': 'a',
            'parcel_type': 'rv',
            'max_persons': 6,
            'has_electricity': True,
            'has_water': True,
            'has_sewage': True,
            'base_price': 35.0,
        })

    def test_parcel_default_state(self):
        self.assertEqual(self.parcel.state, 'available')

    def test_parcel_name_computed(self):
        self.assertTrue(self.parcel.name)
        self.assertIn('A01', self.parcel.name)

    def test_parcel_state_transitions(self):
        self.parcel.state = 'occupied'
        self.assertEqual(self.parcel.state, 'occupied')
        self.parcel.action_set_available()
        self.assertEqual(self.parcel.state, 'available')

    def test_parcel_availability_check(self):
        tomorrow = (datetime.now() + timedelta(days=1)).date()
        next_week = (datetime.now() + timedelta(days=7)).date()
        self.assertTrue(self.parcel.is_available(tomorrow, next_week))


@tagged('post_install', '-at_install')
class TestCampingReservation(TransactionCase):

    def setUp(self):
        super().setUp()
        self.Parcel = self.env['l10n_si.camping.parcel']
        self.Reservation = self.env['l10n_si.camping.reservation']
        self.Partner = self.env['res.partner']

        self.parcel = self.Parcel.create({
            'number': 'B02', 'zone': 'b', 'parcel_type': 'glamping',
            'max_persons': 2, 'base_price': 95.0,
        })
        self.guest = self.Partner.create({'name': 'Camp Test Guest'})
        self.tomorrow = datetime.now() + timedelta(days=1)
        self.next_week = datetime.now() + timedelta(days=5)

    def _create_reservation(self):
        return self.Reservation.create({
            'partner_id': self.guest.id,
            'parcel_id': self.parcel.id,
            'check_in': self.tomorrow,
            'check_out': self.next_week,
            'adults': 2,
            'vehicles': 1,
        })

    def test_reservation_default_state(self):
        res = self._create_reservation()
        self.assertEqual(res.state, 'draft')

    def test_reservation_nights_computed(self):
        res = self._create_reservation()
        delta = self.next_week - self.tomorrow
        self.assertEqual(res.nights, delta.days)

    def test_reservation_confirm(self):
        res = self._create_reservation()
        res.action_confirm()
        self.assertEqual(res.state, 'confirmed')
        self.assertEqual(self.parcel.state, 'reserved')

    def test_reservation_check_in(self):
        res = self._create_reservation()
        res.action_confirm()
        res.action_check_in()
        self.assertEqual(res.state, 'checked_in')
        self.assertEqual(self.parcel.state, 'occupied')

    def test_reservation_check_out(self):
        res = self._create_reservation()
        res.action_confirm()
        res.action_check_in()
        res.action_check_out()
        self.assertEqual(res.state, 'checked_out')
        self.assertEqual(self.parcel.state, 'available')

    def test_reservation_cancel(self):
        res = self._create_reservation()
        res.action_confirm()
        res.action_cancel()
        self.assertEqual(res.state, 'cancelled')

    def test_invalid_dates_raises(self):
        with self.assertRaises(ValidationError):
            self.Reservation.create({
                'partner_id': self.guest.id,
                'parcel_id': self.parcel.id,
                'check_in': self.next_week,
                'check_out': self.tomorrow,
            })
