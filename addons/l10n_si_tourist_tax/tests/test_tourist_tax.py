# -*- coding: utf-8 -*-
"""Tests for l10n_si_tourist_tax — municipality rates and transaction calculation."""
from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestTouristTaxMunicipality(TransactionCase):

    def test_municipality_model_exists(self):
        self.assertTrue(self.env['l10n_si.tourist.tax.municipality'])

    def test_municipality_has_rate_fields(self):
        fields = self.env['l10n_si.tourist.tax.municipality']._fields
        self.assertIn('name', fields)
        self.assertIn('code', fields)
        self.assertIn('rate_adult', fields)
        self.assertIn('rate_youth', fields)
        self.assertIn('rate_child', fields)

    def test_municipality_has_max_nights(self):
        fields = self.env['l10n_si.tourist.tax.municipality']._fields
        self.assertIn('max_chargeable_nights', fields)

    def test_get_rate_for_age_adult(self):
        Municipality = self.env['l10n_si.tourist.tax.municipality']
        mun = Municipality.create({'name': 'Test', 'code': '999', 'rate_adult': 2.50, 'rate_youth': 1.25, 'rate_child': 0.0})
        rate = Municipality.get_rate_for_age(mun.id, 30)
        self.assertEqual(rate, 2.50)

    def test_get_rate_for_age_youth(self):
        Municipality = self.env['l10n_si.tourist.tax.municipality']
        mun = Municipality.create({'name': 'Test', 'code': '999', 'rate_adult': 2.50, 'rate_youth': 1.25, 'rate_child': 0.0})
        rate = Municipality.get_rate_for_age(mun.id, 15)
        self.assertEqual(rate, 1.25)

    def test_get_rate_for_age_child(self):
        Municipality = self.env['l10n_si.tourist.tax.municipality']
        mun = Municipality.create({'name': 'Test', 'code': '999', 'rate_adult': 2.50, 'rate_youth': 1.25, 'rate_child': 0.0})
        rate = Municipality.get_rate_for_age(mun.id, 5)
        self.assertEqual(rate, 0.0)


@tagged('post_install', '-at_install')
class TestTouristTaxTransaction(TransactionCase):

    def test_transaction_model_exists(self):
        self.assertTrue(self.env['l10n_si.tourist.tax.transaction'])

    def test_transaction_has_required_fields(self):
        fields = self.env['l10n_si.tourist.tax.transaction']._fields
        self.assertIn('municipality_id', fields)
        self.assertIn('nights', fields)
        self.assertIn('rate', fields)
        self.assertIn('tax_amount', fields)
        self.assertIn('is_exempt', fields)
        self.assertIn('state', fields)

    def test_transaction_has_exempt_reasons(self):
        field = self.env['l10n_si.tourist.tax.transaction']._fields['exemption_reason']
        selection_keys = [s[0] for s in field.selection]
        self.assertIn('disabled', selection_keys)
        self.assertIn('tour_leader', selection_keys)
        self.assertIn('diplomat', selection_keys)

    def test_calculate_for_stay_method_exists(self):
        self.assertTrue(hasattr(self.env['l10n_si.tourist.tax.transaction'], 'calculate_for_stay'))

    def test_max_nights_cap_applied(self):
        """Chargeable nights should be capped at max_chargeable_nights."""
        Municipality = self.env['l10n_si.tourist.tax.municipality']
        mun = Municipality.create({
            'name': 'Test Cap', 'code': '998',
            'rate_adult': 2.00, 'rate_youth': 1.00, 'rate_child': 0.0,
            'max_chargeable_nights': 7,
        })
        Transaction = self.env['l10n_si.tourist.tax.transaction']
        total, tx_vals = Transaction.calculate_for_stay(
            mun.id, [{'age': 30, 'is_exempt': False}], 10,  # 10 nights but cap is 7
        )
        # Should only charge 7 nights × 2.00 = 14.00
        self.assertEqual(total, 14.0)
        self.assertEqual(tx_vals[0]['chargeable_nights'], 7)
