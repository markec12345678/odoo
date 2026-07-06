# -*- coding: utf-8 -*-
"""Auto-generated basic tests for l10n_si_event_accommodation."""
from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestL10n_siEventAccommodationBlock(TransactionCase):

    def test_model_exists(self):
        self.assertTrue(self.env['l10n_si.event.accommodation.block'])

    def test_has_required_fields(self):
        fields = self.env['l10n_si.event.accommodation.block']._fields
        self.assertIn('name', fields)
        self.assertIn('event_id', fields)
        self.assertIn('company_id', fields)
        self.assertIn('date_from', fields)
        self.assertIn('date_to', fields)

    def test_creation(self):
        record = self.env['l10n_si.event.accommodation.block'].create({'name': 'Test'})
        self.assertEqual(record.name, 'Test')


@tagged('post_install', '-at_install')
class TestL10n_siEventAccommodationReservation(TransactionCase):

    def test_model_exists(self):
        self.assertTrue(self.env['l10n_si.event.accommodation.reservation'])

    def test_has_required_fields(self):
        fields = self.env['l10n_si.event.accommodation.reservation']._fields
        self.assertIn('name', fields)
        self.assertIn('block_id', fields)
        self.assertIn('event_id', fields)
        self.assertIn('partner_id', fields)
        self.assertIn('company_id', fields)

    def test_creation(self):
        record = self.env['l10n_si.event.accommodation.reservation'].create({'name': 'Test'})
        self.assertEqual(record.name, 'Test')

