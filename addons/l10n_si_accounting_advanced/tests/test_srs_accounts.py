# -*- coding: utf-8 -*-
"""Tests for l10n_si_accounting_advanced — SRS accounts and reports."""
from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestSrsAccountModel(TransactionCase):

    def test_model_exists(self):
        self.assertTrue(self.env['l10n_si.srs.account'])

    def test_has_required_fields(self):
        fields = self.env['l10n_si.srs.account']._fields
        self.assertIn('code', fields)
        self.assertIn('name', fields)
        self.assertIn('user_type', fields)
        self.assertIn('srs_category', fields)
        self.assertIn('balance_sheet_position', fields)
        self.assertIn('account_class', fields)

    def test_user_type_selection(self):
        field = self.env['l10n_si.srs.account']._fields['user_type']
        keys = [s[0] for s in field.selection]
        for t in ['asset', 'liability', 'equity', 'income', 'expense']:
            self.assertIn(t, keys)

    def test_srs_category_selection(self):
        field = self.env['l10n_si.srs.account']._fields['srs_category']
        keys = [s[0] for s in field.selection]
        for t in ['balance_sheet', 'income_statement', 'year_end']:
            self.assertIn(t, keys)

    def test_account_creation(self):
        acc = self.env['l10n_si.srs.account'].create({
            'code': '999',
            'name': 'Test konto',
            'user_type': 'equity',
            'srs_category': 'year_end',
            'account_class': '9',
        })
        self.assertEqual(acc.code, '999')
        self.assertEqual(acc.user_type, 'equity')

    def test_display_name_includes_code(self):
        acc = self.env['l10n_si.srs.account'].create({
            'code': '100',
            'name': 'Material',
            'user_type': 'asset',
            'srs_category': 'balance_sheet',
            'account_class': '1',
        })
        self.assertIn('100', acc.display_name)
        self.assertIn('Material', acc.display_name)

    def test_unique_code_per_company(self):
        self.env['l10n_si.srs.account'].create({
            'code': '500', 'name': 'Prihodek', 'user_type': 'income',
            'srs_category': 'income_statement', 'account_class': '5',
        })
        with self.assertRaises(Exception):
            self.env['l10n_si.srs.account'].create({
                'code': '500', 'name': 'Drugi', 'user_type': 'income',
                'srs_category': 'income_statement', 'account_class': '5',
            })

    def test_account_account_has_srs_link(self):
        """account.account should have l10n_si_srs_account_id field."""
        self.assertIn('l10n_si_srs_account_id', self.env['account.account']._fields)
