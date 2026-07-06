# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import hashlib
import re

from odoo.tests import TransactionCase, tagged

from odoo.addons.l10n_si_fiscal.models.account_move import AccountMove


@tagged('post_install', '-at_install')
class TestZoiComputation(TransactionCase):
    """Tests for the FURS ZOI (Zaščitna oznaka izdajatelja računa) algorithm.

    ZOI = MD5(tax_number + issue_datetime + invoice_number +
              business_premise_id + electronic_device_id + invoice_serial)
    All concatenated as strings, no separators. Result is a 32-char lowercase hex.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.slovenia = cls.env.ref('base.si')
        # Use a known-valid SI VAT (passes MOD11 in l10n_si_vat_validation).
        cls.company = cls.env.company
        cls.company.write({
            'country_id': cls.slovenia.id,
            'vat': 'SI10861411',
        })
        cls.premise = cls.env['l10n_si.business.premise'].create({
            'name': 'Test Premise',
            'code': 'BL1',
            'street': 'Slovenska 1',
            'zip': '1000',
            'city': 'Ljubljana',
            'country_id': cls.slovenia.id,
            'company_id': cls.company.id,
        })
        cls.device = cls.env['l10n_si.electronic.device'].create({
            'name': 'Reception 1',
            'code': 'RECEP1',
            'business_premise_id': cls.premise.id,
        })
        cls.partner = cls.env['res.partner'].create({
            'name': 'ZOI Test Partner',
            'country_id': cls.slovenia.id,
        })

    def _create_invoice(self, *, name='BL1-RECEP1-2025-00001', invoice_date=None):
        """Create a minimal out_invoice ready for ZOI computation."""
        move = self.env['account.move'].create({
            'move_type': 'out_invoice',
            'partner_id': self.partner.id,
            'company_id': self.company.id,
            'invoice_date': invoice_date or __import__('datetime').date(2025, 1, 15),
            'l10n_si_business_premise_id': self.premise.id,
            'l10n_si_electronic_device_id': self.device.id,
            'l10n_si_sequence_number': name,
        })
        # name is readonly and assigned by the SI sequence on post; force it for
        # deterministic ZOI tests.
        move.name = name
        return move

    # ------------------------------------------------------------------
    # Serial extraction (pure static method — no DB needed)
    # ------------------------------------------------------------------

    def test_extract_serial_from_reception_number(self):
        """'BL1-RECEP1-2025-00001' → '00001'."""
        serial = AccountMove._si_fiscal_extract_serial('BL1-RECEP1-2025-00001')
        self.assertEqual(serial, '00001')

    def test_extract_serial_from_pos_number(self):
        """'BL1-KASA1-2025-00001' → '00001'."""
        serial = AccountMove._si_fiscal_extract_serial('BL1-KASA1-2025-00001')
        self.assertEqual(serial, '00001')

    def test_extract_serial_no_digits(self):
        """No trailing digits → empty string."""
        serial = AccountMove._si_fiscal_extract_serial('BL1-RECEP1-ABC')
        self.assertEqual(serial, '')

    # ------------------------------------------------------------------
    # ZOI properties
    # ------------------------------------------------------------------

    def test_zoi_is_32_char_lowercase_hex(self):
        """ZOI must be a 32-char lowercase hexadecimal MD5 digest."""
        move = self._create_invoice()
        zoi = move._si_fiscal_compute_zoi()
        self.assertEqual(len(zoi), 32)
        self.assertTrue(re.match(r'^[0-9a-f]{32}$', zoi),
                        f'ZOI {zoi!r} is not 32-char lowercase hex')
        self.assertEqual(zoi, zoi.lower())

    def test_zoi_is_deterministic(self):
        """Same invoice → same ZOI on repeated calls."""
        move = self._create_invoice()
        zoi1 = move._si_fiscal_compute_zoi()
        zoi2 = move._si_fiscal_compute_zoi()
        self.assertEqual(zoi1, zoi2)

    def test_different_invoice_different_zoi(self):
        """Two invoices with different numbers → different ZOI."""
        move1 = self._create_invoice(name='BL1-RECEP1-2025-00001')
        move2 = self._create_invoice(name='BL1-RECEP1-2025-00002')
        zoi1 = move1._si_fiscal_compute_zoi()
        zoi2 = move2._si_fiscal_compute_zoi()
        self.assertNotEqual(zoi1, zoi2)

    def test_field_order_matters(self):
        """ZOI is order-sensitive: swapping tax_no and invoice_number yields a
        different MD5, confirming the concatenation order is significant.
        """
        move = self._create_invoice()
        zoi = move._si_fiscal_compute_zoi()

        tax_no = '10861411'  # 'SI10861411' with prefix stripped
        issue_dt = '2025-01-15T00:00:00'
        invoice_number = 'BL1-RECEP1-2025-00001'
        premise_code = 'BL1'
        device_code = 'RECEP1'
        serial = '00001'

        correct = tax_no + issue_dt + invoice_number + premise_code + device_code + serial
        swapped = invoice_number + issue_dt + tax_no + premise_code + device_code + serial

        self.assertEqual(
            hashlib.md5(correct.encode('utf-8')).hexdigest(), zoi,
            'ZOI must use the FURS spec field order: '
            'tax_no + issue_dt + invoice_number + premise + device + serial.',
        )
        self.assertNotEqual(
            hashlib.md5(correct.encode('utf-8')).hexdigest(),
            hashlib.md5(swapped.encode('utf-8')).hexdigest(),
            'Swapping field order must produce a different digest.',
        )
