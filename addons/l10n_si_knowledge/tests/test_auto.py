# -*- coding: utf-8 -*-
"""Auto-generated basic tests for l10n_si_knowledge."""
from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestL10n_siKnowledgeArticle(TransactionCase):

    def test_model_exists(self):
        self.assertTrue(self.env['l10n_si.knowledge.article'])

    def test_has_required_fields(self):
        fields = self.env['l10n_si.knowledge.article']._fields
        self.assertIn('name', fields)
        self.assertIn('sequence', fields)
        self.assertIn('active', fields)
        self.assertIn('category', fields)
        self.assertIn('parent_id', fields)

    def test_creation(self):
        record = self.env['l10n_si.knowledge.article'].create({'name': 'Test'})
        self.assertEqual(record.name, 'Test')


@tagged('post_install', '-at_install')
class TestL10n_siKnowledgeTag(TransactionCase):

    def test_model_exists(self):
        self.assertTrue(self.env['l10n_si.knowledge.tag'])


@tagged('post_install', '-at_install')
class TestL10n_siKnowledgeTemplate(TransactionCase):

    def test_model_exists(self):
        self.assertTrue(self.env['l10n_si.knowledge.template'])

    def test_has_required_fields(self):
        fields = self.env['l10n_si.knowledge.template']._fields
        self.assertIn('name', fields)
        self.assertIn('template_type', fields)
        self.assertIn('subject', fields)
        self.assertIn('body', fields)
        self.assertIn('placeholders', fields)

    def test_creation(self):
        record = self.env['l10n_si.knowledge.template'].create({'name': 'Test'})
        self.assertEqual(record.name, 'Test')


@tagged('post_install', '-at_install')
class TestL10n_siKnowledgeVersion(TransactionCase):

    def test_model_exists(self):
        self.assertTrue(self.env['l10n_si.knowledge.version'])

