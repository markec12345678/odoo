# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo.exceptions import ValidationError
from odoo.tests import TransactionCase, tagged

from odoo.addons.l10n_si_vat_validation.models.res_partner import _si_mod11_check


@tagged('post_install', '-at_install')
class TestSiVatValidation(TransactionCase):

    def setUp(self):
        super().setUp()
        self.slovenia = self.env.ref('base.si')
        self.partner = self.env['res.partner'].create({
            'name': 'SI Test Partner',
            'country_id': self.slovenia.id,
        })

    def test_mod11_valid_numbers(self):
        # These are well-known valid SI VAT numbers (FURS public test data).
        for valid in ('SI10861411', 'SI54682930', 'SI22867782'):
            with self.subTest(vat=valid):
                digits = valid[2:]
                self.assertTrue(_si_mod11_check(digits), f'{valid} should be valid')

    def test_mod11_invalid_numbers(self):
        # Wrong checksum digit.
        self.assertFalse(_si_mod11_check('12345670'))
        # Too short.
        self.assertFalse(_si_mod11_check('1234567'))
        # All zeros.
        self.assertFalse(_si_mod11_check('00000000'))

    def test_partner_save_valid_vat(self):
        self.partner.vat = 'SI10861411'
        self.assertEqual(self.partner.vat, 'SI10861411')

    def test_partner_save_invalid_vat_raises(self):
        with self.assertRaises(ValidationError):
            self.partner.vat = 'SI12345670'

    def test_partner_save_wrong_format_raises(self):
        with self.assertRaises(ValidationError):
            self.partner.vat = 'SLO12345678'

    def test_non_si_country_skips_check(self):
        # German VAT should not trigger SI validation.
        de = self.env.ref('base.de')
        partner_de = self.env['res.partner'].create({
            'name': 'DE Test',
            'country_id': de.id,
            'vat': 'DE123456789',
        })
        self.assertEqual(partner_de.vat, 'DE123456789')
