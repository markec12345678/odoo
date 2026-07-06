# -*- coding: utf-8 -*-
"""Auto-generated basic tests for l10n_si_hr_roster."""
from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestL10n_siRosterAssignment(TransactionCase):

    def test_model_exists(self):
        self.assertTrue(self.env['l10n_si.roster.assignment'])

    def test_has_required_fields(self):
        fields = self.env['l10n_si.roster.assignment']._fields
        self.assertIn('name', fields)
        self.assertIn('number', fields)
        self.assertIn('company_id', fields)
        self.assertIn('employee_id', fields)
        self.assertIn('shift_id', fields)

    def test_creation(self):
        record = self.env['l10n_si.roster.assignment'].create({'name': 'Test'})
        self.assertEqual(record.name, 'Test')


@tagged('post_install', '-at_install')
class TestL10n_siRosterShift(TransactionCase):

    def test_model_exists(self):
        self.assertTrue(self.env['l10n_si.roster.shift'])

    def test_has_required_fields(self):
        fields = self.env['l10n_si.roster.shift']._fields
        self.assertIn('name', fields)
        self.assertIn('code', fields)
        self.assertIn('active', fields)
        self.assertIn('company_id', fields)
        self.assertIn('start_hour', fields)

    def test_creation(self):
        record = self.env['l10n_si.roster.shift'].create({'name': 'Test'})
        self.assertEqual(record.name, 'Test')


@tagged('post_install', '-at_install')
class TestL10n_siRosterSwapRequest(TransactionCase):

    def test_model_exists(self):
        self.assertTrue(self.env['l10n_si.roster.swap.request'])

