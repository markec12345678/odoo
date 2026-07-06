# -*- coding: utf-8 -*-
"""Auto-generated basic tests for l10n_si_group_booking."""
from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestL10n_siGroupBooking(TransactionCase):

    def test_model_exists(self):
        self.assertTrue(self.env['l10n_si.group.booking'])

    def test_has_required_fields(self):
        fields = self.env['l10n_si.group.booking']._fields
        self.assertIn('name', fields)
        self.assertIn('number', fields)
        self.assertIn('company_id', fields)
        self.assertIn('partner_id', fields)
        self.assertIn('is_travel_agency', fields)

    def test_creation(self):
        record = self.env['l10n_si.group.booking'].create({'name': 'Test'})
        self.assertEqual(record.name, 'Test')


@tagged('post_install', '-at_install')
class TestL10n_siRoomingList(TransactionCase):

    def test_model_exists(self):
        self.assertTrue(self.env['l10n_si.rooming.list'])

    def test_has_required_fields(self):
        fields = self.env['l10n_si.rooming.list']._fields
        self.assertIn('group_booking_id', fields)
        self.assertIn('company_id', fields)
        self.assertIn('partner_id', fields)
        self.assertIn('guest_name', fields)
        self.assertIn('guest_email', fields)

