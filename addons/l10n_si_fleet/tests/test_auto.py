# -*- coding: utf-8 -*-
"""Auto-generated basic tests for l10n_si_fleet."""
from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestL10n_siFleetFuel(TransactionCase):

    def test_model_exists(self):
        self.assertTrue(self.env['l10n_si.fleet.fuel'])

    def test_has_required_fields(self):
        fields = self.env['l10n_si.fleet.fuel']._fields
        self.assertIn('name', fields)
        self.assertIn('vehicle_id', fields)
        self.assertIn('driver_id', fields)
        self.assertIn('date', fields)
        self.assertIn('fuel_type', fields)

    def test_creation(self):
        record = self.env['l10n_si.fleet.fuel'].create({'name': 'Test'})
        self.assertEqual(record.name, 'Test')


@tagged('post_install', '-at_install')
class TestL10n_siFleetInsurance(TransactionCase):

    def test_model_exists(self):
        self.assertTrue(self.env['l10n_si.fleet.insurance'])

    def test_has_required_fields(self):
        fields = self.env['l10n_si.fleet.insurance']._fields
        self.assertIn('name', fields)
        self.assertIn('vehicle_id', fields)
        self.assertIn('insurance_company', fields)
        self.assertIn('policy_number', fields)
        self.assertIn('insurance_type', fields)

    def test_creation(self):
        record = self.env['l10n_si.fleet.insurance'].create({'name': 'Test'})
        self.assertEqual(record.name, 'Test')


@tagged('post_install', '-at_install')
class TestL10n_siFleetMaintenance(TransactionCase):

    def test_model_exists(self):
        self.assertTrue(self.env['l10n_si.fleet.maintenance'])

    def test_has_required_fields(self):
        fields = self.env['l10n_si.fleet.maintenance']._fields
        self.assertIn('name', fields)
        self.assertIn('vehicle_id', fields)
        self.assertIn('date', fields)
        self.assertIn('maintenance_type', fields)
        self.assertIn('odometer', fields)

    def test_creation(self):
        record = self.env['l10n_si.fleet.maintenance'].create({'name': 'Test'})
        self.assertEqual(record.name, 'Test')


@tagged('post_install', '-at_install')
class TestL10n_siFleetTrip(TransactionCase):

    def test_model_exists(self):
        self.assertTrue(self.env['l10n_si.fleet.trip'])

    def test_has_required_fields(self):
        fields = self.env['l10n_si.fleet.trip']._fields
        self.assertIn('name', fields)
        self.assertIn('vehicle_id', fields)
        self.assertIn('driver_id', fields)
        self.assertIn('date_start', fields)
        self.assertIn('date_end', fields)

    def test_creation(self):
        record = self.env['l10n_si.fleet.trip'].create({'name': 'Test'})
        self.assertEqual(record.name, 'Test')

