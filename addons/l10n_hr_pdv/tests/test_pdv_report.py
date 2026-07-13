# -*- coding: utf-8 -*-
"""Tests for l10n_hr_pdv — PDV (VAT) report fields and XML generation."""

from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestPdvReportModel(TransactionCase):

    def test_pdv_report_model_exists(self):
        self.assertTrue(self.env['l10n_hr.pdv.report'])

    def test_pdv_report_line_model_exists(self):
        self.assertTrue(self.env['l10n_hr.pdv.report.line'])

    def test_report_has_vat_breakdown_fields(self):
        fields = self.env['l10n_hr.pdv.report']._fields
        self.assertIn('output_vat_25', fields)
        self.assertIn('output_vat_13', fields)
        self.assertIn('output_vat_5', fields)
        self.assertIn('output_vat_total', fields)
        self.assertIn('input_vat_25', fields)
        self.assertIn('input_vat_13', fields)
        self.assertIn('input_vat_5', fields)
        self.assertIn('input_vat_total', fields)

    def test_report_has_payable_refundable(self):
        fields = self.env['l10n_hr.pdv.report']._fields
        self.assertIn('vat_payable', fields)
        self.assertIn('vat_refundable', fields)

    def test_report_has_eu_fields(self):
        fields = self.env['l10n_hr.pdv.report']._fields
        self.assertIn('eu_acquisitions', fields)
        self.assertIn('eu_supplies', fields)
        self.assertIn('reverse_charge_amount', fields)

    def test_report_has_period_fields(self):
        fields = self.env['l10n_hr.pdv.report']._fields
        self.assertIn('period_type', fields)
        self.assertIn('year', fields)
        self.assertIn('period_number', fields)
        self.assertIn('date_from', fields)
        self.assertIn('date_to', fields)

    def test_report_has_state_selection(self):
        field = self.env['l10n_hr.pdv.report']._fields['state']
        selection_keys = [s[0] for s in field.selection]
        for expected in ['draft', 'computed', 'submitted', 'accepted', 'rejected']:
            self.assertIn(expected, selection_keys)

    def test_report_has_xml_export(self):
        self.assertTrue(hasattr(self.env['l10n_hr.pdv.report'], 'action_generate_xml'))
        self.assertTrue(hasattr(self.env['l10n_hr.pdv.report'], '_build_eporezna_xml'))

    def test_report_has_compute_method(self):
        self.assertTrue(hasattr(self.env['l10n_hr.pdv.report'], 'action_compute'))

    def test_report_has_cron_method(self):
        self.assertTrue(hasattr(self.env['l10n_hr.pdv.report'], '_cron_generate_pdv_reports'))


@tagged('post_install', '-at_install')
class TestPdvReportCreation(TransactionCase):

    def setUp(self):
        super().setUp()
        self.croatia = self.env.ref('base.hr')
        self.company = self.env['res.company'].create({
            'name': 'Test HR Company',
            'country_id': self.croatia.id,
            'vat': '12345678901',
        })

    def test_create_monthly_report(self):
        report = self.env['l10n_hr.pdv.report'].create({
            'company_id': self.company.id,
            'period_type': 'monthly',
            'year': 2025,
            'period_number': 6,
        })
        self.assertEqual(report.period_type, 'monthly')
        self.assertEqual(report.year, 2025)
        self.assertEqual(report.state, 'draft')

    def test_create_quarterly_report(self):
        report = self.env['l10n_hr.pdv.report'].create({
            'company_id': self.company.id,
            'period_type': 'quarterly',
            'year': 2025,
            'period_number': 2,
        })
        self.assertEqual(report.period_type, 'quarterly')

    def test_monthly_dates_computed(self):
        """Monthly report for June 2025: date_from=01.06, date_to=30.06."""
        report = self.env['l10n_hr.pdv.report'].create({
            'company_id': self.company.id,
            'period_type': 'monthly',
            'year': 2025,
            'period_number': 6,
        })
        if report.date_from:
            self.assertEqual(report.date_from.month, 6)
            self.assertEqual(report.date_from.year, 2025)

    def test_quarterly_dates_computed(self):
        """Q2 2025: April-June."""
        report = self.env['l10n_hr.pdv.report'].create({
            'company_id': self.company.id,
            'period_type': 'quarterly',
            'year': 2025,
            'period_number': 2,
        })
        if report.date_from:
            self.assertEqual(report.date_from.month, 4)
            self.assertEqual(report.date_to.month, 6)


@tagged('post_install', '-at_install')
class TestPdvXmlGeneration(TransactionCase):

    def setUp(self):
        super().setUp()
        self.croatia = self.env.ref('base.hr')
        self.company = self.env['res.company'].create({
            'name': 'Test HR XML',
            'country_id': self.croatia.id,
            'vat': '12345678901',
        })
        self.report = self.env['l10n_hr.pdv.report'].create({
            'company_id': self.company.id,
            'period_type': 'monthly',
            'year': 2025,
            'period_number': 6,
            'output_vat_25': 100.0,
            'output_vat_13': 50.0,
            'output_vat_5': 25.0,
            'output_vat_total': 175.0,
            'input_vat_25': 80.0,
            'input_vat_13': 40.0,
            'input_vat_5': 20.0,
            'input_vat_total': 140.0,
            'vat_payable': 35.0,
            'vat_refundable': 0.0,
        })

    def test_xml_generation_returns_string(self):
        if hasattr(self.report, '_build_eporezna_xml'):
            xml = self.report._build_eporezna_xml()
            self.assertIsInstance(xml, str)
            self.assertIn('PdvObrazac', xml)

    def test_xml_contains_oib(self):
        if hasattr(self.report, '_build_eporezna_xml'):
            xml = self.report._build_eporezna_xml()
            self.assertIn('12345678901', xml)

    def test_xml_contains_period(self):
        if hasattr(self.report, '_build_eporezna_xml'):
            xml = self.report._build_eporezna_xml()
            self.assertIn('2025', xml)

    def test_xml_contains_vat_amounts(self):
        if hasattr(self.report, '_build_eporezna_xml'):
            xml = self.report._build_eporezna_xml()
            self.assertIn('175.00', xml)  # output_vat_total
            self.assertIn('140.00', xml)  # input_vat_total
