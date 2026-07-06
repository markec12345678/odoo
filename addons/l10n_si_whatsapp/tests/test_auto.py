# -*- coding: utf-8 -*-
"""Auto-generated basic tests for l10n_si_whatsapp."""
from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestL10n_siWhatsappMessage(TransactionCase):

    def test_model_exists(self):
        self.assertTrue(self.env['l10n_si.whatsapp.message'])

    def test_has_required_fields(self):
        fields = self.env['l10n_si.whatsapp.message']._fields
        self.assertIn('partner_id', fields)
        self.assertIn('phone', fields)
        self.assertIn('direction', fields)
        self.assertIn('body', fields)
        self.assertIn('template_id', fields)


@tagged('post_install', '-at_install')
class TestL10n_siWhatsappTemplate(TransactionCase):

    def test_model_exists(self):
        self.assertTrue(self.env['l10n_si.whatsapp.template'])

    def test_has_required_fields(self):
        fields = self.env['l10n_si.whatsapp.template']._fields
        self.assertIn('name', fields)
        self.assertIn('body', fields)
        self.assertIn('language', fields)
        self.assertIn('category', fields)
        self.assertIn('active', fields)

    def test_creation(self):
        record = self.env['l10n_si.whatsapp.template'].create({'name': 'Test'})
        self.assertEqual(record.name, 'Test')

