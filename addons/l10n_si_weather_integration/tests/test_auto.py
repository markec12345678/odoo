# -*- coding: utf-8 -*-
"""Auto-generated basic tests for l10n_si_weather_integration."""
from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestL10n_siWeatherForecast(TransactionCase):

    def test_model_exists(self):
        self.assertTrue(self.env['l10n_si.weather.forecast'])

    def test_has_required_fields(self):
        fields = self.env['l10n_si.weather.forecast']._fields
        self.assertIn('name', fields)
        self.assertIn('number', fields)
        self.assertIn('active', fields)
        self.assertIn('company_id', fields)
        self.assertIn('notes', fields)

    def test_creation(self):
        record = self.env['l10n_si.weather.forecast'].create({'name': 'Test'})
        self.assertEqual(record.name, 'Test')

