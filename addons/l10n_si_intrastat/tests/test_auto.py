# -*- coding: utf-8 -*-
"""Auto-generated basic tests for l10n_si_intrastat."""
from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestL10n_siIntrastatLine(TransactionCase):

    def test_model_exists(self):
        self.assertTrue(self.env['l10n_si.intrastat.line'])


@tagged('post_install', '-at_install')
class TestL10n_siIntrastatReport(TransactionCase):

    def test_model_exists(self):
        self.assertTrue(self.env['l10n_si.intrastat.report'])

    def test_has_required_fields(self):
        fields = self.env['l10n_si.intrastat.report']._fields
        self.assertIn('name', fields)
        self.assertIn('number', fields)
        self.assertIn('year', fields)
        self.assertIn('month', fields)
        self.assertIn('report_type', fields)

    def test_creation(self):
        record = self.env['l10n_si.intrastat.report'].create({'name': 'Test'})
        self.assertEqual(record.name, 'Test')

