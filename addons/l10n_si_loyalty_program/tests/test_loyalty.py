# -*- coding: utf-8 -*-
"""Tests for l10n_si_loyalty_program — member, transaction, reward."""
from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestLoyaltyModels(TransactionCase):

    def test_member_model_exists(self):
        self.assertTrue(self.env['l10n_si.loyalty.member'])

    def test_transaction_model_exists(self):
        self.assertTrue(self.env['l10n_si.loyalty.transaction'])

    def test_reward_model_exists(self):
        self.assertTrue(self.env['l10n_si.loyalty.reward'])


@tagged('post_install', '-at_install')
class TestLoyaltyMember(TransactionCase):

    def test_member_has_tier_field(self):
        fields = self.env['l10n_si.loyalty.member']._fields
        self.assertIn('tier', fields)

    def test_member_has_points_field(self):
        fields = self.env['l10n_si.loyalty.member']._fields
        self.assertIn('points', fields)

    def test_tier_selection_has_bronze_silver_gold(self):
        field = self.env['l10n_si.loyalty.member']._fields['tier']
        keys = [s[0] for s in field.selection]
        for t in ['bronze', 'silver', 'gold', 'platinum']:
            self.assertIn(t, keys, f'Missing tier: {t}')


@tagged('post_install', '-at_install')
class TestLoyaltyTransaction(TransactionCase):

    def test_transaction_has_type(self):
        fields = self.env['l10n_si.loyalty.transaction']._fields
        self.assertIn('transaction_type', fields)

    def test_transaction_has_points(self):
        fields = self.env['l10n_si.loyalty.transaction']._fields
        self.assertIn('points', fields)


@tagged('post_install', '-at_install')
class TestLoyaltyReward(TransactionCase):

    def test_reward_has_name(self):
        fields = self.env['l10n_si.loyalty.reward']._fields
        self.assertIn('name', fields)

    def test_reward_has_points_cost(self):
        fields = self.env['l10n_si.loyalty.reward']._fields
        self.assertIn('points_cost', fields)

    def test_reward_creation(self):
        reward = self.env['l10n_si.loyalty.reward'].create({
            'name': 'Brezplačen zajtrk',
            'points_cost': 100,
        })
        self.assertEqual(reward.name, 'Brezplačen zajtrk')
        self.assertEqual(reward.points_cost, 100)
