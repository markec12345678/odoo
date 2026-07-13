# -*- coding: utf-8 -*-
"""Unit tests for ZKI (Zaštitni kod izdavatelja računa) computation.

ZKI = MD5(oib + datum_vrijeme + broj_racuna + oznaka_pp + oznaka_nu +
          ukupni_iznos + ukupni_porez)

Reference: CISF Technical specification v1.8, section 3.1
"""
import hashlib

from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestZkiAlgorithm(TransactionCase):

    def _compute_zki(self, oib, dt_str, inv, pp, nu, total, tax):
        total_str = f'{total:.2f}'
        tax_str = f'{tax:.2f}'
        concat = oib + dt_str + inv + pp + nu + total_str + tax_str
        return hashlib.md5(concat.encode('utf-8')).hexdigest()

    def test_zki_is_32_char_hex(self):
        zki = self._compute_zki('12345678901', '15.01.2025 00:00:00', '00001', 'POS1', '1', 100.0, 25.0)
        self.assertRegex(zki, r'^[0-9a-f]{32}$')

    def test_zki_deterministic(self):
        args = ('12345678901', '15.01.2025 00:00:00', '00001', 'POS1', '1', 100.0, 25.0)
        self.assertEqual(self._compute_zki(*args), self._compute_zki(*args))

    def test_different_invoice_different_zki(self):
        zki1 = self._compute_zki('12345678901', '15.01.2025 00:00:00', '00001', 'POS1', '1', 100.0, 25.0)
        zki2 = self._compute_zki('12345678901', '15.01.2025 00:00:00', '00002', 'POS1', '1', 100.0, 25.0)
        self.assertNotEqual(zki1, zki2)

    def test_different_premise_different_zki(self):
        zki1 = self._compute_zki('12345678901', '15.01.2025 00:00:00', '00001', 'POS1', '1', 100.0, 25.0)
        zki2 = self._compute_zki('12345678901', '15.01.2025 00:00:00', '00001', 'POS2', '1', 100.0, 25.0)
        self.assertNotEqual(zki1, zki2)

    def test_different_amount_different_zki(self):
        zki1 = self._compute_zki('12345678901', '15.01.2025 00:00:00', '00001', 'POS1', '1', 100.0, 25.0)
        zki2 = self._compute_zki('12345678901', '15.01.2025 00:00:00', '00001', 'POS1', '1', 200.0, 25.0)
        self.assertNotEqual(zki1, zki2)

    def test_field_order_matters(self):
        correct = self._compute_zki('12345678901', '15.01.2025 00:00:00', '00001', 'POS1', '1', 100.0, 25.0)
        # Swap premise and device
        wrong = hashlib.md5(('12345678901' + '15.01.2025 00:00:00' + '00001' + '1' + 'POS1' + '100.00' + '25.00').encode()).hexdigest()
        self.assertNotEqual(correct, wrong)

    def test_total_format_2_decimals(self):
        self.assertEqual(f'{100.5:.2f}', '100.50')
        self.assertEqual(f'{99.999:.2f}', '100.00')


@tagged('post_install', '-at_install')
class TestHrFiscalFields(TransactionCase):

    def test_account_move_has_hr_fiscal_fields(self):
        fields = self.env['account.move']._fields
        self.assertIn('l10n_hr_zki', fields)
        self.assertIn('l10n_hr_jir', fields)
        self.assertIn('l10n_hr_fiscal_state', fields)
        self.assertIn('l10n_hr_business_premise_id', fields)

    def test_company_has_hr_fiscal_config(self):
        fields = self.env['res.company']._fields
        self.assertIn('hr_fiscal_enabled', fields)
        self.assertIn('hr_fiscal_environment', fields)
        self.assertIn('hr_fiscal_certificate', fields)
        self.assertIn('hr_fiscal_auto_submit', fields)

    def test_business_premise_model_exists(self):
        self.assertTrue(self.env['l10n_hr.business.premise'])

    def test_fiscal_log_model_exists(self):
        self.assertTrue(self.env['l10n_hr.fiscal.log'])
