# -*- coding: utf-8 -*-
"""Tests for l10n_si_event_venue — venue, hall, event, booking."""
from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestEventVenueModels(TransactionCase):

    def test_venue_model_exists(self):
        self.assertTrue(self.env['l10n_si.event.venue'])

    def test_hall_model_exists(self):
        self.assertTrue(self.env['l10n_si.event.hall'])

    def test_event_model_exists(self):
        self.assertTrue(self.env['l10n_si.event.event'])

    def test_booking_model_exists(self):
        self.assertTrue(self.env['l10n_si.event.booking'])

    def test_catering_model_exists(self):
        self.assertTrue(self.env['l10n_si.event.catering.line'])

    def test_package_model_exists(self):
        self.assertTrue(self.env['l10n_si.event.package'])

    def test_menu_item_model_exists(self):
        self.assertTrue(self.env['l10n_si.event.menu.item'])


@tagged('post_install', '-at_install')
class TestEventVenueCreation(TransactionCase):

    def test_venue_creation(self):
        venue = self.env['l10n_si.event.venue'].create({
            'name': 'Grand Hall Ljubljana',
        })
        self.assertEqual(venue.name, 'Grand Hall Ljubljana')

    def test_hall_creation(self):
        hall = self.env['l10n_si.event.hall'].create({
            'name': 'Dvorana A',
        })
        self.assertEqual(hall.name, 'Dvorana A')

    def test_event_creation(self):
        event = self.env['l10n_si.event.event'].create({
            'name': 'Poroka 2025',
        })
        self.assertEqual(event.name, 'Poroka 2025')


@tagged('post_install', '-at_install')
class TestEventBooking(TransactionCase):

    def test_booking_has_state(self):
        fields = self.env['l10n_si.event.booking']._fields
        self.assertIn('state', fields)

    def test_booking_state_selection(self):
        field = self.env['l10n_si.event.booking']._fields['state']
        keys = [s[0] for s in field.selection]
        self.assertTrue(len(keys) > 0)
