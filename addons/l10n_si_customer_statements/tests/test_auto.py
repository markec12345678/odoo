# -*- coding: utf-8 -*-
"""Auto-generated basic tests for l10n_si_customer_statements."""
from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestL10n_siCustomerStatement(TransactionCase):

    def test_model_exists(self):
        self.assertTrue(self.env['l10n_si.customer.statement'])

    def test_has_required_fields(self):
        fields = self.env['l10n_si.customer.statement']._fields
        self.assertIn('name', fields)
        self.assertIn('partner_id', fields)
        self.assertIn('company_id', fields)
        self.assertIn('date_from', fields)
        self.assertIn('date_to', fields)

    def test_creation(self):
        record = self.env['l10n_si.customer.statement'].create({'name': 'Test'})
        self.assertEqual(record.name, 'Test')


@tagged('post_install', '-at_install')
class TestL10n_siCustomerStatementLine(TransactionCase):

    def test_model_exists(self):
        self.assertTrue(self.env['l10n_si.customer.statement.line'])

