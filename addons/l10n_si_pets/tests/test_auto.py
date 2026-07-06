# -*- coding: utf-8 -*-
"""Auto-generated basic tests for l10n_si_pets."""
from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestL10n_siPet(TransactionCase):

    def test_model_exists(self):
        self.assertTrue(self.env['l10n_si.pet'])

    def test_has_required_fields(self):
        fields = self.env['l10n_si.pet']._fields
        self.assertIn('name', fields)
        self.assertIn('number', fields)
        self.assertIn('active', fields)
        self.assertIn('company_id', fields)
        self.assertIn('notes', fields)

    def test_creation(self):
        record = self.env['l10n_si.pet'].create({'name': 'Test'})
        self.assertEqual(record.name, 'Test')

