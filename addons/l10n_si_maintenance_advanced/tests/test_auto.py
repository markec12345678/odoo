# -*- coding: utf-8 -*-
"""Auto-generated basic tests for l10n_si_maintenance_advanced."""
from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestL10n_siMaintenancePartLine(TransactionCase):

    def test_model_exists(self):
        self.assertTrue(self.env['l10n_si.maintenance.part.line'])

    def test_has_required_fields(self):
        fields = self.env['l10n_si.maintenance.part.line']._fields
        self.assertIn('si_serial_number', fields)
        self.assertIn('si_acquisition_date', fields)
        self.assertIn('si_acquisition_value', fields)
        self.assertIn('si_warranty_expiry', fields)
        self.assertIn('si_location', fields)


@tagged('post_install', '-at_install')
class TestL10n_siMaintenanceSchedule(TransactionCase):

    def test_model_exists(self):
        self.assertTrue(self.env['l10n_si.maintenance.schedule'])

    def test_has_required_fields(self):
        fields = self.env['l10n_si.maintenance.schedule']._fields
        self.assertIn('name', fields)
        self.assertIn('equipment_id', fields)
        self.assertIn('active', fields)
        self.assertIn('company_id', fields)
        self.assertIn('frequency', fields)

    def test_creation(self):
        record = self.env['l10n_si.maintenance.schedule'].create({'name': 'Test'})
        self.assertEqual(record.name, 'Test')

