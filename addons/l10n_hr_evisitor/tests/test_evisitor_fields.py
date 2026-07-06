# -*- coding: utf-8 -*-
"""Tests for l10n_hr_evisitor module — field existence and model verification."""
from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestEvisitorModels(TransactionCase):

    def test_accommodation_model_exists(self):
        self.assertTrue(self.env['l10n_hr.evisitor.accommodation'])

    def test_guest_registration_model_exists(self):
        self.assertTrue(self.env['l10n_hr.evisitor.guest.registration'])

    def test_log_model_exists(self):
        self.assertTrue(self.env['l10n_hr.evisitor.log'])

    def test_accommodation_has_required_fields(self):
        fields = self.env['l10n_hr.evisitor.accommodation']._fields
        self.assertIn('name', fields)
        self.assertIn('htz_id', fields)
        self.assertIn('accommodation_type', fields)
        self.assertIn('capacity_beds', fields)
        self.assertIn('tourist_tax_adult', fields)
        self.assertIn('evisitor_username', fields)
        self.assertIn('environment', fields)

    def test_registration_has_lifecycle_fields(self):
        fields = self.env['l10n_hr.evisitor.guest.registration']._fields
        self.assertIn('arrival_date', fields)
        self.assertIn('departure_date', fields)
        self.assertIn('nights', fields)
        self.assertIn('evisitor_status', fields)
        self.assertIn('evisitor_submission_id', fields)
        self.assertIn('tourist_tax_amount', fields)

    def test_company_has_evisitor_config(self):
        fields = self.env['res.company']._fields
        for f in ['l10n_hr_evisitor_environment', 'l10n_hr_evisitor_auto_register',
                   'l10n_hr_evisitor_auto_deregister']:
            self.assertIn(f, fields, f'Missing company field: {f}')

    def test_registration_status_selection(self):
        field = self.env['l10n_hr.evisitor.guest.registration']._fields['evisitor_status']
        selection_keys = [s[0] for s in field.selection]
        for expected in ['draft', 'pending', 'submitted', 'deregistered', 'error']:
            self.assertIn(expected, selection_keys, f'Missing status: {expected}')
