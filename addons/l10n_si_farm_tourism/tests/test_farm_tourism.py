# -*- coding: utf-8 -*-
"""Tests for l10n_si_farm_tourism — farm room, product, and reservation."""
from datetime import datetime, timedelta

from odoo.exceptions import ValidationError
from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestFarmRoom(TransactionCase):

    def setUp(self):
        super().setUp()
        self.Room = self.env['l10n_si.farm.room']
        self.room = self.Room.create({
            'name': 'Soba 1',
            'number': '1',
            'price_per_night': 45.0,
            'capacity': 2,
        })

    def test_room_default_state(self):
        self.assertEqual(self.room.state, 'available')

    def test_room_price(self):
        self.assertEqual(self.room.price_per_night, 45.0)


@tagged('post_install', '-at_install')
class TestFarmProduct(TransactionCase):

    def test_product_model_exists(self):
        self.assertTrue(self.env['l10n_si.farm.product'])

    def test_product_creation(self):
        product = self.env['l10n_si.farm.product'].create({
            'name': 'Domači sir',
            'price': 8.50,
        })
        self.assertEqual(product.name, 'Domači sir')
        self.assertEqual(product.price, 8.50)


@tagged('post_install', '-at_install')
class TestFarmReservation(TransactionCase):

    def setUp(self):
        super().setUp()
        self.Room = self.env['l10n_si.farm.room']
        self.Reservation = self.env['l10n_si.farm.reservation']
        self.Partner = self.env['res.partner']

        self.room = self.Room.create({
            'name': 'Test', 'number': '1', 'price_per_night': 45.0, 'capacity': 2,
        })
        self.guest = self.Partner.create({'name': 'Farm Guest'})
        self.tomorrow = datetime.now() + timedelta(days=1)
        self.next_week = datetime.now() + timedelta(days=4)

    def test_reservation_default_state(self):
        res = self.Reservation.create({
            'partner_id': self.guest.id,
            'room_id': self.room.id,
            'check_in': self.tomorrow,
            'check_out': self.next_week,
        })
        self.assertEqual(res.state, 'draft')

    def test_reservation_confirm(self):
        res = self.Reservation.create({
            'partner_id': self.guest.id,
            'room_id': self.room.id,
            'check_in': self.tomorrow,
            'check_out': self.next_week,
        })
        res.action_confirm()
        self.assertEqual(res.state, 'confirmed')

    def test_reservation_check_in_out(self):
        res = self.Reservation.create({
            'partner_id': self.guest.id,
            'room_id': self.room.id,
            'check_in': self.tomorrow,
            'check_out': self.next_week,
        })
        res.action_confirm()
        res.action_check_in()
        self.assertEqual(res.state, 'checked_in')
        res.action_check_out()
        self.assertEqual(res.state, 'checked_out')

    def test_invalid_dates_raises(self):
        with self.assertRaises(ValidationError):
            self.Reservation.create({
                'partner_id': self.guest.id,
                'room_id': self.room.id,
                'check_in': self.next_week,
                'check_out': self.tomorrow,
            })
