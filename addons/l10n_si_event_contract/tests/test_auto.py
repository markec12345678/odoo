# -*- coding: utf-8 -*-
"""Auto-generated basic tests for l10n_si_event_contract."""
from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestL10n_siEventContract(TransactionCase):

    def test_model_exists(self):
        self.assertTrue(self.env['l10n_si.event.contract'])

    def test_has_required_fields(self):
        fields = self.env['l10n_si.event.contract']._fields
        self.assertIn('name', fields)
        self.assertIn('number', fields)
        self.assertIn('event_id', fields)
        self.assertIn('template_id', fields)
        self.assertIn('company_id', fields)

    def test_creation(self):
        record = self.env['l10n_si.event.contract'].create({'name': 'Test'})
        self.assertEqual(record.name, 'Test')


@tagged('post_install', '-at_install')
class TestL10n_siEventContractTemplate(TransactionCase):

    def test_model_exists(self):
        self.assertTrue(self.env['l10n_si.event.contract.template'])

    def test_has_required_fields(self):
        fields = self.env['l10n_si.event.contract.template']._fields
        self.assertIn('name', fields)
        self.assertIn('code', fields)
        self.assertIn('active', fields)
        self.assertIn('contract_type', fields)
        self.assertIn('body', fields)

    def test_creation(self):
        record = self.env['l10n_si.event.contract.template'].create({'name': 'Test'})
        self.assertEqual(record.name, 'Test')

