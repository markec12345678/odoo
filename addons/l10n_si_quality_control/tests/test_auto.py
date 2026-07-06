# -*- coding: utf-8 -*-
"""Auto-generated basic tests for l10n_si_quality_control."""
from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestL10n_siQualityCheck(TransactionCase):

    def test_model_exists(self):
        self.assertTrue(self.env['l10n_si.quality.check'])

    def test_has_required_fields(self):
        fields = self.env['l10n_si.quality.check']._fields
        self.assertIn('name', fields)
        self.assertIn('number', fields)
        self.assertIn('check_type', fields)
        self.assertIn('product_id', fields)
        self.assertIn('lot_id', fields)

    def test_creation(self):
        record = self.env['l10n_si.quality.check'].create({'name': 'Test'})
        self.assertEqual(record.name, 'Test')


@tagged('post_install', '-at_install')
class TestL10n_siQualityCheckLine(TransactionCase):

    def test_model_exists(self):
        self.assertTrue(self.env['l10n_si.quality.check.line'])


@tagged('post_install', '-at_install')
class TestL10n_siQualityNonconformance(TransactionCase):

    def test_model_exists(self):
        self.assertTrue(self.env['l10n_si.quality.nonconformance'])

    def test_has_required_fields(self):
        fields = self.env['l10n_si.quality.nonconformance']._fields
        self.assertIn('name', fields)
        self.assertIn('number', fields)
        self.assertIn('check_id', fields)
        self.assertIn('product_id', fields)
        self.assertIn('lot_id', fields)

    def test_creation(self):
        record = self.env['l10n_si.quality.nonconformance'].create({'name': 'Test'})
        self.assertEqual(record.name, 'Test')

