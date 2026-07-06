# -*- coding: utf-8 -*-
"""Auto-generated basic tests for l10n_si_accessibility."""
from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestL10n_siAccessibilityFeature(TransactionCase):

    def test_model_exists(self):
        self.assertTrue(self.env['l10n_si.accessibility.feature'])

    def test_has_required_fields(self):
        fields = self.env['l10n_si.accessibility.feature']._fields
        self.assertIn('name', fields)
        self.assertIn('number', fields)
        self.assertIn('active', fields)
        self.assertIn('company_id', fields)
        self.assertIn('notes', fields)

    def test_creation(self):
        record = self.env['l10n_si.accessibility.feature'].create({'name': 'Test'})
        self.assertEqual(record.name, 'Test')

