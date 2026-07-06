# -*- coding: utf-8 -*-
"""Auto-generated basic tests for l10n_si_event_photographer."""
from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestL10n_siEventVendor(TransactionCase):

    def test_model_exists(self):
        self.assertTrue(self.env['l10n_si.event.vendor'])

    def test_has_required_fields(self):
        fields = self.env['l10n_si.event.vendor']._fields
        self.assertIn('name', fields)
        self.assertIn('active', fields)
        self.assertIn('partner_id', fields)
        self.assertIn('company_id', fields)
        self.assertIn('category', fields)

    def test_creation(self):
        record = self.env['l10n_si.event.vendor'].create({'name': 'Test'})
        self.assertEqual(record.name, 'Test')


@tagged('post_install', '-at_install')
class TestL10n_siEventVendorBooking(TransactionCase):

    def test_model_exists(self):
        self.assertTrue(self.env['l10n_si.event.vendor.booking'])

    def test_has_required_fields(self):
        fields = self.env['l10n_si.event.vendor.booking']._fields
        self.assertIn('name', fields)
        self.assertIn('event_id', fields)
        self.assertIn('vendor_id', fields)
        self.assertIn('company_id', fields)
        self.assertIn('date', fields)

    def test_creation(self):
        record = self.env['l10n_si.event.vendor.booking'].create({'name': 'Test'})
        self.assertEqual(record.name, 'Test')

