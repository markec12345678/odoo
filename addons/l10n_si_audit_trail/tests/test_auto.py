# -*- coding: utf-8 -*-
"""Auto-generated basic tests for l10n_si_audit_trail."""
from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestL10n_siAuditTrail(TransactionCase):

    def test_model_exists(self):
        self.assertTrue(self.env['l10n_si.audit.trail'])

    def test_has_required_fields(self):
        fields = self.env['l10n_si.audit.trail']._fields
        self.assertIn('name', fields)
        self.assertIn('user_id', fields)
        self.assertIn('model_name', fields)
        self.assertIn('record_id', fields)
        self.assertIn('record_name', fields)

    def test_creation(self):
        record = self.env['l10n_si.audit.trail'].create({'name': 'Test'})
        self.assertEqual(record.name, 'Test')

