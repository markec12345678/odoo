# -*- coding: utf-8 -*-
"""Auto-generated basic tests for l10n_si_payment_gateway."""
from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestL10n_siPaymentConfig(TransactionCase):

    def test_model_exists(self):
        self.assertTrue(self.env['l10n_si.payment.config'])

    def test_has_required_fields(self):
        fields = self.env['l10n_si.payment.config']._fields
        self.assertIn('name', fields)
        self.assertIn('sequence', fields)
        self.assertIn('active', fields)
        self.assertIn('company_id', fields)
        self.assertIn('provider', fields)

    def test_creation(self):
        record = self.env['l10n_si.payment.config'].create({'name': 'Test'})
        self.assertEqual(record.name, 'Test')


@tagged('post_install', '-at_install')
class TestL10n_siPaymentTransaction(TransactionCase):

    def test_model_exists(self):
        self.assertTrue(self.env['l10n_si.payment.transaction'])

    def test_has_required_fields(self):
        fields = self.env['l10n_si.payment.transaction']._fields
        self.assertIn('name', fields)
        self.assertIn('config_id', fields)
        self.assertIn('company_id', fields)
        self.assertIn('partner_id', fields)
        self.assertIn('move_id', fields)

    def test_creation(self):
        record = self.env['l10n_si.payment.transaction'].create({'name': 'Test'})
        self.assertEqual(record.name, 'Test')

