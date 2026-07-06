# -*- coding: utf-8 -*-
"""Auto-generated basic tests for l10n_si_website_booking."""
from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestL10n_siBookingPromo(TransactionCase):

    def test_model_exists(self):
        self.assertTrue(self.env['l10n_si.booking.promo'])

    def test_has_required_fields(self):
        fields = self.env['l10n_si.booking.promo']._fields
        self.assertIn('name', fields)
        self.assertIn('code', fields)
        self.assertIn('active', fields)
        self.assertIn('company_id', fields)
        self.assertIn('discount_type', fields)

    def test_creation(self):
        record = self.env['l10n_si.booking.promo'].create({'name': 'Test'})
        self.assertEqual(record.name, 'Test')


@tagged('post_install', '-at_install')
class TestL10n_siBookingPromoUsage(TransactionCase):

    def test_model_exists(self):
        self.assertTrue(self.env['l10n_si.booking.promo.usage'])

