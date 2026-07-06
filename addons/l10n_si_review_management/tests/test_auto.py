# -*- coding: utf-8 -*-
"""Auto-generated basic tests for l10n_si_review_management."""
from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestL10n_siReview(TransactionCase):

    def test_model_exists(self):
        self.assertTrue(self.env['l10n_si.review'])

    def test_has_required_fields(self):
        fields = self.env['l10n_si.review']._fields
        self.assertIn('name', fields)
        self.assertIn('number', fields)
        self.assertIn('company_id', fields)
        self.assertIn('source_id', fields)
        self.assertIn('source_platform', fields)

    def test_creation(self):
        record = self.env['l10n_si.review'].create({'name': 'Test'})
        self.assertEqual(record.name, 'Test')


@tagged('post_install', '-at_install')
class TestL10n_siReviewImage(TransactionCase):

    def test_model_exists(self):
        self.assertTrue(self.env['l10n_si.review.image'])


@tagged('post_install', '-at_install')
class TestL10n_siReviewSource(TransactionCase):

    def test_model_exists(self):
        self.assertTrue(self.env['l10n_si.review.source'])

    def test_has_required_fields(self):
        fields = self.env['l10n_si.review.source']._fields
        self.assertIn('name', fields)
        self.assertIn('sequence', fields)
        self.assertIn('active', fields)
        self.assertIn('company_id', fields)
        self.assertIn('platform', fields)

    def test_creation(self):
        record = self.env['l10n_si.review.source'].create({'name': 'Test'})
        self.assertEqual(record.name, 'Test')

