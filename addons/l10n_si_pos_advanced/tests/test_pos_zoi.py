# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import hashlib
import re

from odoo.tests import TransactionCase, tagged

from odoo.addons.l10n_si_fiscal.models.account_move import AccountMove


def _compute_zoi_pure(tax_no, issue_dt_str, invoice_number, premise_code, device_code, serial):
    """Pure-Python reimplementation of the FURS ZOI algorithm.

    Mirrors ``AccountMove._si_fiscal_compute_zoi`` but takes primitive
    strings, so it can be exercised without touching the database.
    """
    concatenated = tax_no + issue_dt_str + invoice_number + premise_code + device_code + serial
    return hashlib.md5(concatenated.encode('utf-8')).hexdigest()


@tagged('post_install', '-at_install')
class TestPosZoi(TransactionCase):
    """ZOI algorithm tests that apply equally to POS orders, plus field
    presence checks on pos.order and pos.config.
    """

    # ------------------------------------------------------------------
    # Pure algorithm tests (no DB needed)
    # ------------------------------------------------------------------

    def test_zoi_is_32_char_hex(self):
        """ZOI produced by the pure algorithm is a 32-char lowercase hex string."""
        zoi = _compute_zoi_pure(
            '10861411', '2025-01-15T00:00:00',
            'BL1-KASA1-2025-00001', 'BL1', 'KASA1', '00001',
        )
        self.assertEqual(len(zoi), 32)
        self.assertTrue(re.match(r'^[0-9a-f]{32}$', zoi),
                        f'ZOI {zoi!r} is not 32-char lowercase hex')

    def test_different_invoice_different_zoi(self):
        """Two invoices differing only in invoice_serial produce different ZOIs."""
        zoi1 = _compute_zoi_pure(
            '10861411', '2025-01-15T00:00:00',
            'BL1-KASA1-2025-00001', 'BL1', 'KASA1', '00001',
        )
        zoi2 = _compute_zoi_pure(
            '10861411', '2025-01-15T00:00:00',
            'BL1-KASA1-2025-00002', 'BL1', 'KASA1', '00002',
        )
        self.assertNotEqual(zoi1, zoi2)

    # ------------------------------------------------------------------
    # Serial extraction (reuses the fiscal helper directly)
    # ------------------------------------------------------------------

    def test_extract_serial_from_pos_number(self):
        """'BL1-KASA1-2025-00001' → '00001'."""
        serial = AccountMove._si_fiscal_extract_serial('BL1-KASA1-2025-00001')
        self.assertEqual(serial, '00001')

    # ------------------------------------------------------------------
    # Field presence on POS models
    # ------------------------------------------------------------------

    def test_pos_order_has_l10n_si_zoi_field(self):
        """pos.order must expose the l10n_si_zoi Char field added by the
        l10n_si_pos_advanced override.
        """
        pos_order_fields = self.env['pos.order']._fields
        self.assertIn('l10n_si_zoi', pos_order_fields,
                      'pos.order is missing the l10n_si_zoi field.')

    def test_pos_config_has_si_fiscal_enabled_field(self):
        """pos.config must expose the si_fiscal_enabled Boolean toggle."""
        pos_config_fields = self.env['pos.config']._fields
        self.assertIn('si_fiscal_enabled', pos_config_fields,
                      'pos.config is missing the si_fiscal_enabled field.')
