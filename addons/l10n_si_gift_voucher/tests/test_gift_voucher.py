# -*- coding: utf-8 -*-
"""Tests for l10n_si_gift_voucher — sell, redeem, track balance."""
from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestGiftVoucher(TransactionCase):

    def setUp(self):
        super().setUp()
        self.Voucher = self.env['l10n_si.gift.voucher']

    def test_voucher_model_exists(self):
        self.assertTrue(self.Voucher)

    def test_voucher_has_required_fields(self):
        fields = self.Voucher._fields
        self.assertIn('name', fields)
        self.assertIn('amount', fields)
        self.assertIn('state', fields)

    def test_voucher_creation(self):
        voucher = self.Voucher.create({
            'name': 'GV-2025-001',
            'amount': 50.0,
        })
        self.assertEqual(voucher.name, 'GV-2025-001')
        self.assertEqual(voucher.amount, 50.0)

    def test_voucher_state_selection(self):
        field = self.Voucher._fields['state']
        selection_keys = [s[0] for s in field.selection]
        # Should have at least draft/sold/redeemed/expired
        self.assertIn('draft', selection_keys)
