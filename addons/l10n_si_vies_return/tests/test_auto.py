# -*- coding: utf-8 -*-
"""Auto-generated basic tests for l10n_si_vies_return."""
from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestL10n_siViesLine(TransactionCase):

    def test_model_exists(self):
        self.assertTrue(self.env['l10n_si.vies.line'])


@tagged('post_install', '-at_install')
class TestL10n_siViesReturn(TransactionCase):

    def test_model_exists(self):
        self.assertTrue(self.env['l10n_si.vies.return'])

    def test_has_required_fields(self):
        fields = self.env['l10n_si.vies.return']._fields
        self.assertIn('name', fields)
        self.assertIn('number', fields)
        self.assertIn('year', fields)
        self.assertIn('month', fields)
        self.assertIn('company_id', fields)

    def test_creation(self):
        record = self.env['l10n_si.vies.return'].create({'name': 'Test'})
        self.assertEqual(record.name, 'Test')

