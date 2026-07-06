# -*- coding: utf-8 -*-
"""Auto-generated basic tests for l10n_si_year_end_close."""
from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestL10n_siYearEndClose(TransactionCase):

    def test_model_exists(self):
        self.assertTrue(self.env['l10n_si.year.end.close'])

    def test_has_required_fields(self):
        fields = self.env['l10n_si.year.end.close']._fields
        self.assertIn('name', fields)
        self.assertIn('number', fields)
        self.assertIn('year', fields)
        self.assertIn('company_id', fields)
        self.assertIn('state', fields)

    def test_creation(self):
        record = self.env['l10n_si.year.end.close'].create({'name': 'Test'})
        self.assertEqual(record.name, 'Test')

