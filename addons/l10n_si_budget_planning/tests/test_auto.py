# -*- coding: utf-8 -*-
"""Auto-generated basic tests for l10n_si_budget_planning."""
from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestL10n_siBudget(TransactionCase):

    def test_model_exists(self):
        self.assertTrue(self.env['l10n_si.budget'])

    def test_has_required_fields(self):
        fields = self.env['l10n_si.budget']._fields
        self.assertIn('name', fields)
        self.assertIn('number', fields)
        self.assertIn('year', fields)
        self.assertIn('department', fields)
        self.assertIn('company_id', fields)

    def test_creation(self):
        record = self.env['l10n_si.budget'].create({'name': 'Test'})
        self.assertEqual(record.name, 'Test')


@tagged('post_install', '-at_install')
class TestL10n_siBudgetLine(TransactionCase):

    def test_model_exists(self):
        self.assertTrue(self.env['l10n_si.budget.line'])

    def test_has_required_fields(self):
        fields = self.env['l10n_si.budget.line']._fields
        self.assertIn('budget_id', fields)
        self.assertIn('company_id', fields)
        self.assertIn('name', fields)
        self.assertIn('sequence', fields)
        self.assertIn('line_type', fields)

    def test_creation(self):
        record = self.env['l10n_si.budget.line'].create({'name': 'Test'})
        self.assertEqual(record.name, 'Test')

