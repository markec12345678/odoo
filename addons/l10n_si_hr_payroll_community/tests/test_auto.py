# -*- coding: utf-8 -*-
"""Auto-generated basic tests for l10n_si_hr_payroll_community."""
from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestL10n_siPayrollRule(TransactionCase):

    def test_model_exists(self):
        self.assertTrue(self.env['l10n_si.payroll.rule'])

    def test_has_required_fields(self):
        fields = self.env['l10n_si.payroll.rule']._fields
        self.assertIn('name', fields)
        self.assertIn('code', fields)
        self.assertIn('sequence', fields)
        self.assertIn('structure_id', fields)
        self.assertIn('category', fields)

    def test_creation(self):
        record = self.env['l10n_si.payroll.rule'].create({'name': 'Test'})
        self.assertEqual(record.name, 'Test')


@tagged('post_install', '-at_install')
class TestL10n_siPayrollStructure(TransactionCase):

    def test_model_exists(self):
        self.assertTrue(self.env['l10n_si.payroll.structure'])

    def test_has_required_fields(self):
        fields = self.env['l10n_si.payroll.structure']._fields
        self.assertIn('name', fields)
        self.assertIn('code', fields)
        self.assertIn('description', fields)
        self.assertIn('rule_ids', fields)
        self.assertIn('active', fields)

    def test_creation(self):
        record = self.env['l10n_si.payroll.structure'].create({'name': 'Test'})
        self.assertEqual(record.name, 'Test')


@tagged('post_install', '-at_install')
class TestL10n_siPayslip(TransactionCase):

    def test_model_exists(self):
        self.assertTrue(self.env['l10n_si.payslip'])

