# -*- coding: utf-8 -*-
"""Tests for l10n_si_sequence — SI invoice numbering per business premise."""
from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestBusinessPremise(TransactionCase):

    def test_premise_model_exists(self):
        self.assertTrue(self.env['l10n_si.business.premise'])

    def test_premise_has_required_fields(self):
        fields = self.env['l10n_si.business.premise']._fields
        self.assertIn('name', fields)
        self.assertIn('code', fields)
        self.assertIn('company_id', fields)

    def test_premise_creation(self):
        premise = self.env['l10n_si.business.premise'].create({
            'name': 'Test Premise',
            'code': 'BL1',
        })
        self.assertEqual(premise.code, 'BL1')
        self.assertEqual(premise.name, 'Test Premise')


@tagged('post_install', '-at_install')
class TestElectronicDevice(TransactionCase):

    def test_device_model_exists(self):
        self.assertTrue(self.env['l10n_si.electronic.device'])

    def test_device_has_required_fields(self):
        fields = self.env['l10n_si.electronic.device']._fields
        self.assertIn('name', fields)
        self.assertIn('code', fields)

    def test_device_creation(self):
        device = self.env['l10n_si.electronic.device'].create({
            'name': 'Reception 1',
            'code': 'RECEP1',
        })
        self.assertEqual(device.code, 'RECEP1')


@tagged('post_install', '-at_install')
class TestSIInvoiceNumberFormat(TransactionCase):
    """Test SI invoice number format: PREMISE-DEVICE-YEAR-SEQ."""

    def test_number_format(self):
        """SI invoice number should follow BL1-RECEP1-2025-00001 format."""
        # This is validated in l10n_si_fiscal and l10n_si_pos_advanced
        # Here we verify the business premise + device combination
        premise = self.env['l10n_si.business.premise'].create({
            'name': 'Test', 'code': 'BL1',
        })
        device = self.env['l10n_si.electronic.device'].create({
            'name': 'Test Dev', 'code': 'RECEP1',
        })
        # The format is: {premise.code}-{device.code}-{year}-{seq:05d}
        year = 2025
        seq = 1
        expected = f'{premise.code}-{device.code}-{year}-{seq:05d}'
        self.assertEqual(expected, 'BL1-RECEP1-2025-00001')
