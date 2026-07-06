# -*- coding: utf-8 -*-
"""Auto-generated basic tests for l10n_si_transport."""
from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestL10n_siTransportBooking(TransactionCase):

    def test_model_exists(self):
        self.assertTrue(self.env['l10n_si.transport.booking'])

    def test_has_required_fields(self):
        fields = self.env['l10n_si.transport.booking']._fields
        self.assertIn('name', fields)
        self.assertIn('number', fields)
        self.assertIn('company_id', fields)
        self.assertIn('partner_id', fields)
        self.assertIn('hotel_folio_id', fields)

    def test_creation(self):
        record = self.env['l10n_si.transport.booking'].create({'name': 'Test'})
        self.assertEqual(record.name, 'Test')

