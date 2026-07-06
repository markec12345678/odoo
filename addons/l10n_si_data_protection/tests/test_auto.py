# -*- coding: utf-8 -*-
"""Auto-generated basic tests for l10n_si_data_protection."""
from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestL10n_siGdprConsent(TransactionCase):

    def test_model_exists(self):
        self.assertTrue(self.env['l10n_si.gdpr.consent'])

    def test_has_required_fields(self):
        fields = self.env['l10n_si.gdpr.consent']._fields
        self.assertIn('partner_id', fields)
        self.assertIn('company_id', fields)
        self.assertIn('consent_type', fields)
        self.assertIn('state', fields)
        self.assertIn('granted_on', fields)


@tagged('post_install', '-at_install')
class TestL10n_siGdprRequest(TransactionCase):

    def test_model_exists(self):
        self.assertTrue(self.env['l10n_si.gdpr.request'])

    def test_has_required_fields(self):
        fields = self.env['l10n_si.gdpr.request']._fields
        self.assertIn('name', fields)
        self.assertIn('number', fields)
        self.assertIn('company_id', fields)
        self.assertIn('partner_id', fields)
        self.assertIn('request_type', fields)

    def test_creation(self):
        record = self.env['l10n_si.gdpr.request'].create({'name': 'Test'})
        self.assertEqual(record.name, 'Test')

