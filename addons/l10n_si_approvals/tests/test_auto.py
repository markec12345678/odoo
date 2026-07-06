# -*- coding: utf-8 -*-
"""Auto-generated basic tests for l10n_si_approvals."""
from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestL10n_siApprovalRequest(TransactionCase):

    def test_model_exists(self):
        self.assertTrue(self.env['l10n_si.approval.request'])

    def test_has_required_fields(self):
        fields = self.env['l10n_si.approval.request']._fields
        self.assertIn('name', fields)
        self.assertIn('number', fields)
        self.assertIn('category', fields)
        self.assertIn('company_id', fields)
        self.assertIn('requester_employee_id', fields)

    def test_creation(self):
        record = self.env['l10n_si.approval.request'].create({'name': 'Test'})
        self.assertEqual(record.name, 'Test')


@tagged('post_install', '-at_install')
class TestL10n_siApprovalRule(TransactionCase):

    def test_model_exists(self):
        self.assertTrue(self.env['l10n_si.approval.rule'])

    def test_has_required_fields(self):
        fields = self.env['l10n_si.approval.rule']._fields
        self.assertIn('name', fields)
        self.assertIn('active', fields)
        self.assertIn('company_id', fields)
        self.assertIn('category', fields)
        self.assertIn('min_amount', fields)

    def test_creation(self):
        record = self.env['l10n_si.approval.rule'].create({'name': 'Test'})
        self.assertEqual(record.name, 'Test')


@tagged('post_install', '-at_install')
class TestL10n_siApprovalRuleApprover(TransactionCase):

    def test_model_exists(self):
        self.assertTrue(self.env['l10n_si.approval.rule.approver'])


@tagged('post_install', '-at_install')
class TestL10n_siApprovalStep(TransactionCase):

    def test_model_exists(self):
        self.assertTrue(self.env['l10n_si.approval.step'])

