# -*- coding: utf-8 -*-
"""Auto-generated basic tests for l10n_si_procurement."""
from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestL10n_siProcurementContract(TransactionCase):

    def test_model_exists(self):
        self.assertTrue(self.env['l10n_si.procurement.contract'])

    def test_has_required_fields(self):
        fields = self.env['l10n_si.procurement.contract']._fields
        self.assertIn('name', fields)
        self.assertIn('number', fields)
        self.assertIn('vendor_id', fields)
        self.assertIn('company_id', fields)
        self.assertIn('date_from', fields)

    def test_creation(self):
        record = self.env['l10n_si.procurement.contract'].create({'name': 'Test'})
        self.assertEqual(record.name, 'Test')


@tagged('post_install', '-at_install')
class TestL10n_siProcurementItem(TransactionCase):

    def test_model_exists(self):
        self.assertTrue(self.env['l10n_si.procurement.item'])

    def test_has_required_fields(self):
        fields = self.env['l10n_si.procurement.item']._fields
        self.assertIn('name', fields)
        self.assertIn('code', fields)
        self.assertIn('active', fields)
        self.assertIn('company_id', fields)
        self.assertIn('product_id', fields)

    def test_creation(self):
        record = self.env['l10n_si.procurement.item'].create({'name': 'Test'})
        self.assertEqual(record.name, 'Test')


@tagged('post_install', '-at_install')
class TestL10n_siProcurementVendor(TransactionCase):

    def test_model_exists(self):
        self.assertTrue(self.env['l10n_si.procurement.vendor'])

    def test_has_required_fields(self):
        fields = self.env['l10n_si.procurement.vendor']._fields
        self.assertIn('name', fields)
        self.assertIn('active', fields)
        self.assertIn('partner_id', fields)
        self.assertIn('company_id', fields)
        self.assertIn('contact_name', fields)

    def test_creation(self):
        record = self.env['l10n_si.procurement.vendor'].create({'name': 'Test'})
        self.assertEqual(record.name, 'Test')

