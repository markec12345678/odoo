# -*- coding: utf-8 -*-
"""Auto-generated basic tests for l10n_si_event_equipment_rental."""
from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestL10n_siEventEquipment(TransactionCase):

    def test_model_exists(self):
        self.assertTrue(self.env['l10n_si.event.equipment'])

    def test_has_required_fields(self):
        fields = self.env['l10n_si.event.equipment']._fields
        self.assertIn('name', fields)
        self.assertIn('code', fields)
        self.assertIn('active', fields)
        self.assertIn('company_id', fields)
        self.assertIn('product_id', fields)

    def test_creation(self):
        record = self.env['l10n_si.event.equipment'].create({'name': 'Test'})
        self.assertEqual(record.name, 'Test')


@tagged('post_install', '-at_install')
class TestL10n_siEventEquipmentRental(TransactionCase):

    def test_model_exists(self):
        self.assertTrue(self.env['l10n_si.event.equipment.rental'])

    def test_has_required_fields(self):
        fields = self.env['l10n_si.event.equipment.rental']._fields
        self.assertIn('name', fields)
        self.assertIn('event_id', fields)
        self.assertIn('partner_id', fields)
        self.assertIn('company_id', fields)
        self.assertIn('date_from', fields)

    def test_creation(self):
        record = self.env['l10n_si.event.equipment.rental'].create({'name': 'Test'})
        self.assertEqual(record.name, 'Test')


@tagged('post_install', '-at_install')
class TestL10n_siEventEquipmentRentalLine(TransactionCase):

    def test_model_exists(self):
        self.assertTrue(self.env['l10n_si.event.equipment.rental.line'])

