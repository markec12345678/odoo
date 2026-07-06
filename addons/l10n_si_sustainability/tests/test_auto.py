# -*- coding: utf-8 -*-
"""Auto-generated basic tests for l10n_si_sustainability."""
from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestL10n_siSustainabilityCertificate(TransactionCase):

    def test_model_exists(self):
        self.assertTrue(self.env['l10n_si.sustainability.certificate'])

    def test_has_required_fields(self):
        fields = self.env['l10n_si.sustainability.certificate']._fields
        self.assertIn('name', fields)
        self.assertIn('cert_type', fields)
        self.assertIn('level', fields)
        self.assertIn('valid_from', fields)
        self.assertIn('valid_to', fields)

    def test_creation(self):
        record = self.env['l10n_si.sustainability.certificate'].create({'name': 'Test'})
        self.assertEqual(record.name, 'Test')


@tagged('post_install', '-at_install')
class TestL10n_siSustainabilityMetric(TransactionCase):

    def test_model_exists(self):
        self.assertTrue(self.env['l10n_si.sustainability.metric'])

    def test_has_required_fields(self):
        fields = self.env['l10n_si.sustainability.metric']._fields
        self.assertIn('name', fields)
        self.assertIn('date', fields)
        self.assertIn('company_id', fields)
        self.assertIn('metric_type', fields)
        self.assertIn('quantity', fields)

    def test_creation(self):
        record = self.env['l10n_si.sustainability.metric'].create({'name': 'Test'})
        self.assertEqual(record.name, 'Test')

