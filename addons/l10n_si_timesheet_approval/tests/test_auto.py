# -*- coding: utf-8 -*-
"""Auto-generated basic tests for l10n_si_timesheet_approval."""
from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestL10n_siTimesheetWeek(TransactionCase):

    def test_model_exists(self):
        self.assertTrue(self.env['l10n_si.timesheet.week'])

    def test_has_required_fields(self):
        fields = self.env['l10n_si.timesheet.week']._fields
        self.assertIn('name', fields)
        self.assertIn('employee_id', fields)
        self.assertIn('date_start', fields)
        self.assertIn('date_end', fields)
        self.assertIn('week_number', fields)

    def test_creation(self):
        record = self.env['l10n_si.timesheet.week'].create({'name': 'Test'})
        self.assertEqual(record.name, 'Test')

