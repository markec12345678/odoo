# -*- coding: utf-8 -*-
"""Auto-generated basic tests for l10n_si_assets."""
from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestL10n_siAsset(TransactionCase):

    def test_model_exists(self):
        self.assertTrue(self.env['l10n_si.asset'])


@tagged('post_install', '-at_install')
class TestL10n_siAssetCategory(TransactionCase):

    def test_model_exists(self):
        self.assertTrue(self.env['l10n_si.asset.category'])

    def test_has_required_fields(self):
        fields = self.env['l10n_si.asset.category']._fields
        self.assertIn('name', fields)
        self.assertIn('code', fields)
        self.assertIn('active', fields)
        self.assertIn('company_id', fields)
        self.assertIn('depreciation_method', fields)

    def test_creation(self):
        record = self.env['l10n_si.asset.category'].create({'name': 'Test'})
        self.assertEqual(record.name, 'Test')


@tagged('post_install', '-at_install')
class TestL10n_siAssetDepreciationLine(TransactionCase):

    def test_model_exists(self):
        self.assertTrue(self.env['l10n_si.asset.depreciation.line'])

