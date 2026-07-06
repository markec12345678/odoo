# -*- coding: utf-8 -*-
"""Auto-generated basic tests for l10n_si_concierge_services."""
from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestL10n_siConciergeRequest(TransactionCase):

    def test_model_exists(self):
        self.assertTrue(self.env['l10n_si.concierge.request'])

    def test_has_required_fields(self):
        fields = self.env['l10n_si.concierge.request']._fields
        self.assertIn('name', fields)
        self.assertIn('number', fields)
        self.assertIn('company_id', fields)
        self.assertIn('partner_id', fields)
        self.assertIn('hotel_folio_id', fields)

    def test_creation(self):
        record = self.env['l10n_si.concierge.request'].create({'name': 'Test'})
        self.assertEqual(record.name, 'Test')

