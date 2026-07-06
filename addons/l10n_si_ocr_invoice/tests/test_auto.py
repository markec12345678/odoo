# -*- coding: utf-8 -*-
"""Auto-generated basic tests for l10n_si_ocr_invoice."""
from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestL10n_siOcrDocument(TransactionCase):

    def test_model_exists(self):
        self.assertTrue(self.env['l10n_si.ocr.document'])

    def test_has_required_fields(self):
        fields = self.env['l10n_si.ocr.document']._fields
        self.assertIn('name', fields)
        self.assertIn('state', fields)
        self.assertIn('pdf_attachment_id', fields)
        self.assertIn('page_count', fields)
        self.assertIn('extracted_text', fields)

    def test_creation(self):
        record = self.env['l10n_si.ocr.document'].create({'name': 'Test'})
        self.assertEqual(record.name, 'Test')

