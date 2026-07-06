# -*- coding: utf-8 -*-
"""Auto-generated basic tests for l10n_si_marketing_automation."""
from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestL10n_siMarketingCampaign(TransactionCase):

    def test_model_exists(self):
        self.assertTrue(self.env['l10n_si.marketing.campaign'])

    def test_has_required_fields(self):
        fields = self.env['l10n_si.marketing.campaign']._fields
        self.assertIn('name', fields)
        self.assertIn('active', fields)
        self.assertIn('company_id', fields)
        self.assertIn('trigger', fields)
        self.assertIn('domain', fields)

    def test_creation(self):
        record = self.env['l10n_si.marketing.campaign'].create({'name': 'Test'})
        self.assertEqual(record.name, 'Test')


@tagged('post_install', '-at_install')
class TestL10n_siMarketingCampaignParticipant(TransactionCase):

    def test_model_exists(self):
        self.assertTrue(self.env['l10n_si.marketing.campaign.participant'])


@tagged('post_install', '-at_install')
class TestL10n_siMarketingCampaignStep(TransactionCase):

    def test_model_exists(self):
        self.assertTrue(self.env['l10n_si.marketing.campaign.step'])

