# -*- coding: utf-8 -*-
"""Auto-generated basic tests for l10n_si_helpdesk_simple."""
from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestL10n_siHelpdeskCannedResponse(TransactionCase):

    def test_model_exists(self):
        self.assertTrue(self.env['l10n_si.helpdesk.canned.response'])

    def test_has_required_fields(self):
        fields = self.env['l10n_si.helpdesk.canned.response']._fields
        self.assertIn('name', fields)
        self.assertIn('body', fields)
        self.assertIn('team_ids', fields)
        self.assertIn('active', fields)

    def test_creation(self):
        record = self.env['l10n_si.helpdesk.canned.response'].create({'name': 'Test'})
        self.assertEqual(record.name, 'Test')


@tagged('post_install', '-at_install')
class TestL10n_siHelpdeskStage(TransactionCase):

    def test_model_exists(self):
        self.assertTrue(self.env['l10n_si.helpdesk.stage'])

    def test_has_required_fields(self):
        fields = self.env['l10n_si.helpdesk.stage']._fields
        self.assertIn('name', fields)
        self.assertIn('sequence', fields)
        self.assertIn('is_close', fields)
        self.assertIn('is_default', fields)
        self.assertIn('fold', fields)

    def test_creation(self):
        record = self.env['l10n_si.helpdesk.stage'].create({'name': 'Test'})
        self.assertEqual(record.name, 'Test')


@tagged('post_install', '-at_install')
class TestL10n_siHelpdeskTag(TransactionCase):

    def test_model_exists(self):
        self.assertTrue(self.env['l10n_si.helpdesk.tag'])


@tagged('post_install', '-at_install')
class TestL10n_siHelpdeskTeam(TransactionCase):

    def test_model_exists(self):
        self.assertTrue(self.env['l10n_si.helpdesk.team'])

    def test_has_required_fields(self):
        fields = self.env['l10n_si.helpdesk.team']._fields
        self.assertIn('name', fields)
        self.assertIn('sequence', fields)
        self.assertIn('active', fields)
        self.assertIn('company_id', fields)
        self.assertIn('description', fields)

    def test_creation(self):
        record = self.env['l10n_si.helpdesk.team'].create({'name': 'Test'})
        self.assertEqual(record.name, 'Test')


@tagged('post_install', '-at_install')
class TestL10n_siHelpdeskTicket(TransactionCase):

    def test_model_exists(self):
        self.assertTrue(self.env['l10n_si.helpdesk.ticket'])

    def test_has_required_fields(self):
        fields = self.env['l10n_si.helpdesk.ticket']._fields
        self.assertIn('name', fields)
        self.assertIn('number', fields)
        self.assertIn('description', fields)
        self.assertIn('team_id', fields)
        self.assertIn('user_id', fields)

    def test_creation(self):
        record = self.env['l10n_si.helpdesk.ticket'].create({'name': 'Test'})
        self.assertEqual(record.name, 'Test')

