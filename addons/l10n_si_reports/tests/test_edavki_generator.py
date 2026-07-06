# -*- coding: utf-8 -*-
"""Tests for l10n_si_reports — eDavki XML generators (REK-1, M4)."""
from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestReportModels(TransactionCase):

    def test_report_log_model_exists(self):
        self.assertTrue(self.env['l10n_si.report.log'])

    def test_report_log_has_report_types(self):
        field = self.env['l10n_si.report.log']._fields['report_type']
        selection_keys = [s[0] for s in field.selection]
        self.assertIn('rek1', selection_keys)
        self.assertIn('m4', selection_keys)
        self.assertIn('ajpes_srs', selection_keys)

    def test_report_log_has_states(self):
        field = self.env['l10n_si.report.log']._fields['state']
        selection_keys = [s[0] for s in field.selection]
        for expected in ['draft', 'generated', 'submitted', 'accepted', 'rejected']:
            self.assertIn(expected, selection_keys)


@tagged('post_install', '-at_install')
class TestEdavkiGenerators(TransactionCase):

    def setUp(self):
        super().setUp()
        self.slovenia = self.env.ref('base.si')
        self.company = self.env['res.company'].create({
            'name': 'Test SI eDavki',
            'country_id': self.slovenia.id,
            'vat': 'SI10861411',
        })

    def test_rek1_generator_exists(self):
        """REK-1 generator class should be available."""
        from odoo.addons.l10n_si_reports.models.l10n_si_edavki_generator import L10nSiRek1Generator
        self.assertTrue(L10nSiRek1Generator)

    def test_m4_generator_exists(self):
        """M4 generator class should be available."""
        from odoo.addons.l10n_si_reports.models.l10n_si_edavki_generator import L10nSiM4Generator
        self.assertTrue(L10nSiM4Generator)

    def test_report_log_has_generate_xml_action(self):
        """L10nSiReportLog should have action_generate_xml method."""
        log = self.env['l10n_si.report.log']
        self.assertTrue(hasattr(log, 'action_generate_xml'))

    def test_report_log_has_quick_actions(self):
        log = self.env['l10n_si.report.log']
        self.assertTrue(hasattr(log, 'action_generate_rek1_current_month'))
        self.assertTrue(hasattr(log, 'action_generate_m4_current_month'))


@tagged('post_install', '-at_install')
class TestReportLogCreation(TransactionCase):

    def setUp(self):
        super().setUp()
        self.slovenia = self.env.ref('base.si')
        self.company = self.env['res.company'].create({
            'name': 'Test SI Report Log',
            'country_id': self.slovenia.id,
        })

    def test_create_rek1_log(self):
        from datetime import date
        log = self.env['l10n_si.report.log'].create({
            'report_type': 'rek1',
            'company_id': self.company.id,
            'date_from': date(2025, 6, 1),
            'date_to': date(2025, 6, 30),
        })
        self.assertEqual(log.report_type, 'rek1')
        self.assertEqual(log.state, 'generated')  # default

    def test_create_m4_log(self):
        from datetime import date
        log = self.env['l10n_si.report.log'].create({
            'report_type': 'm4',
            'company_id': self.company.id,
            'date_from': date(2025, 6, 1),
            'date_to': date(2025, 6, 30),
        })
        self.assertEqual(log.report_type, 'm4')

    def test_log_has_xml_attachment_field(self):
        fields = self.env['l10n_si.report.log']._fields
        self.assertIn('xml_attachment_id', fields)

    def test_log_has_pdf_attachment_field(self):
        fields = self.env['l10n_si.report.log']._fields
        self.assertIn('pdf_attachment_id', fields)
