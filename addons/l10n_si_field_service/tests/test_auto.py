# -*- coding: utf-8 -*-
"""Auto-generated basic tests for l10n_si_field_service."""
from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestL10n_siFieldServiceMaterial(TransactionCase):

    def test_model_exists(self):
        self.assertTrue(self.env['l10n_si.field.service.material'])


@tagged('post_install', '-at_install')
class TestL10n_siFieldServiceOrder(TransactionCase):

    def test_model_exists(self):
        self.assertTrue(self.env['l10n_si.field.service.order'])

    def test_has_required_fields(self):
        fields = self.env['l10n_si.field.service.order']._fields
        self.assertIn('name', fields)
        self.assertIn('number', fields)
        self.assertIn('partner_id', fields)
        self.assertIn('partner_address', fields)
        self.assertIn('contact_phone', fields)

    def test_creation(self):
        record = self.env['l10n_si.field.service.order'].create({'name': 'Test'})
        self.assertEqual(record.name, 'Test')


@tagged('post_install', '-at_install')
class TestL10n_siFieldServicePhoto(TransactionCase):

    def test_model_exists(self):
        self.assertTrue(self.env['l10n_si.field.service.photo'])

