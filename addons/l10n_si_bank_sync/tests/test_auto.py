# -*- coding: utf-8 -*-
"""Auto-generated basic tests for l10n_si_bank_sync."""
from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestL10n_siBankSyncConfig(TransactionCase):

    def test_model_exists(self):
        self.assertTrue(self.env['l10n_si.bank.sync.config'])

    def test_has_required_fields(self):
        fields = self.env['l10n_si.bank.sync.config']._fields
        self.assertIn('name', fields)
        self.assertIn('bank_code', fields)
        self.assertIn('iban', fields)
        self.assertIn('journal_id', fields)
        self.assertIn('company_id', fields)

    def test_creation(self):
        record = self.env['l10n_si.bank.sync.config'].create({'name': 'Test'})
        self.assertEqual(record.name, 'Test')


@tagged('post_install', '-at_install')
class TestL10n_siBankSyncLog(TransactionCase):

    def test_model_exists(self):
        self.assertTrue(self.env['l10n_si.bank.sync.log'])

    def test_has_required_fields(self):
        fields = self.env['l10n_si.bank.sync.log']._fields
        self.assertIn('config_id', fields)
        self.assertIn('company_id', fields)
        self.assertIn('date_from', fields)
        self.assertIn('date_to', fields)
        self.assertIn('state', fields)

