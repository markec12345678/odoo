# -*- coding: utf-8 -*-
"""Auto-generated basic tests for l10n_si_subscription_advanced."""
from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestL10n_siSubscription(TransactionCase):

    def test_model_exists(self):
        self.assertTrue(self.env['l10n_si.subscription'])

    def test_has_required_fields(self):
        fields = self.env['l10n_si.subscription']._fields
        self.assertIn('name', fields)
        self.assertIn('number', fields)
        self.assertIn('partner_id', fields)
        self.assertIn('plan_id', fields)
        self.assertIn('company_id', fields)

    def test_creation(self):
        record = self.env['l10n_si.subscription'].create({'name': 'Test'})
        self.assertEqual(record.name, 'Test')


@tagged('post_install', '-at_install')
class TestL10n_siSubscriptionPlan(TransactionCase):

    def test_model_exists(self):
        self.assertTrue(self.env['l10n_si.subscription.plan'])

    def test_has_required_fields(self):
        fields = self.env['l10n_si.subscription.plan']._fields
        self.assertIn('name', fields)
        self.assertIn('sequence', fields)
        self.assertIn('active', fields)
        self.assertIn('product_id', fields)
        self.assertIn('description', fields)

    def test_creation(self):
        record = self.env['l10n_si.subscription.plan'].create({'name': 'Test'})
        self.assertEqual(record.name, 'Test')

