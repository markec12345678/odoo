# -*- coding: utf-8 -*-
"""Auto-generated basic tests for l10n_si_sign."""
from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestL10n_siSignRequest(TransactionCase):

    def test_model_exists(self):
        self.assertTrue(self.env['l10n_si.sign.request'])

    def test_has_required_fields(self):
        fields = self.env['l10n_si.sign.request']._fields
        self.assertIn('name', fields)
        self.assertIn('reference', fields)
        self.assertIn('partner_id', fields)
        self.assertIn('company_id', fields)
        self.assertIn('document_attachment_id', fields)

    def test_creation(self):
        record = self.env['l10n_si.sign.request'].create({'name': 'Test'})
        self.assertEqual(record.name, 'Test')


@tagged('post_install', '-at_install')
class TestL10n_siSignSignature(TransactionCase):

    def test_model_exists(self):
        self.assertTrue(self.env['l10n_si.sign.signature'])

