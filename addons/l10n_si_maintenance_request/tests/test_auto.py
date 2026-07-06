# -*- coding: utf-8 -*-
"""Auto-generated basic tests for l10n_si_maintenance_request."""
from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestL10n_siMaintenanceRequest(TransactionCase):

    def test_model_exists(self):
        self.assertTrue(self.env['l10n_si.maintenance.request'])

    def test_has_required_fields(self):
        fields = self.env['l10n_si.maintenance.request']._fields
        self.assertIn('name', fields)
        self.assertIn('number', fields)
        self.assertIn('company_id', fields)
        self.assertIn('partner_id', fields)
        self.assertIn('reported_by_user_id', fields)

    def test_creation(self):
        record = self.env['l10n_si.maintenance.request'].create({'name': 'Test'})
        self.assertEqual(record.name, 'Test')


@tagged('post_install', '-at_install')
class TestL10n_siMaintenanceRequestPhoto(TransactionCase):

    def test_model_exists(self):
        self.assertTrue(self.env['l10n_si.maintenance.request.photo'])

