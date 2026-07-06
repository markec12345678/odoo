# -*- coding: utf-8 -*-
"""Tests for l10n_si_wellness — services, bookings, passes."""
from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestWellnessService(TransactionCase):

    def test_service_model_exists(self):
        self.assertTrue(self.env['l10n_si.wellness.service'])

    def test_service_has_fields(self):
        fields = self.env['l10n_si.wellness.service']._fields
        self.assertIn('name', fields)

    def test_service_creation(self):
        svc = self.env['l10n_si.wellness.service'].create({
            'name': 'Klasična masaža 30min',
        })
        self.assertEqual(svc.name, 'Klasična masaža 30min')


@tagged('post_install', '-at_install')
class TestWellnessBooking(TransactionCase):

    def test_booking_model_exists(self):
        self.assertTrue(self.env['l10n_si.wellness.booking'])

    def test_booking_has_fields(self):
        fields = self.env['l10n_si.wellness.booking']._fields
        self.assertIn('state', fields)

    def test_booking_state_selection(self):
        field = self.env['l10n_si.wellness.booking']._fields['state']
        keys = [s[0] for s in field.selection]
        self.assertTrue(len(keys) > 0)


@tagged('post_install', '-at_install')
class TestWellnessPass(TransactionCase):

    def test_pass_model_exists(self):
        self.assertTrue(self.env['l10n_si.wellness.pass'])

    def test_pass_has_fields(self):
        fields = self.env['l10n_si.wellness.pass']._fields
        self.assertIn('name', fields)
