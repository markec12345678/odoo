# -*- coding: utf-8 -*-
"""Tests for AI Concierge conversation workflow with rule-based fallback."""
from unittest.mock import patch, MagicMock

from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestAIConversationFallback(TransactionCase):
    """Test rule-based fallback when no AI key is configured."""

    def setUp(self):
        super().setUp()
        self.Config = self.env['l10n_si.ai.concierge.config']
        self.Conversation = self.env['l10n_si.ai.concierge.conversation']

        self.config = self.Config.create({
            'name': 'Test Concierge',
            'ai_backend': 'zai',
            'api_key': '',
            'system_prompt': 'Si AI asistent v hotelu.',
        })
        self.conversation = self.Conversation.create({
            'config_id': self.config.id,
            'state': 'active',
        })

    def test_wifi_query(self):
        response = self.conversation._call_ai_for_response('Kakšno je wifi geslo?')
        self.assertIn('Gost2025', response)

    def test_zajtrk_query(self):
        response = self.conversation._call_ai_for_response('Kdaj je zajtrk?')
        self.assertIn('7:00', response)

    def test_checkin_query(self):
        response = self.conversation._call_ai_for_response('Kdaj je check-in?')
        self.assertIn('14:00', response)

    def test_wellness_query(self):
        response = self.conversation._call_ai_for_response('Kdaj je odprt wellness?')
        self.assertIn('9:00', response)

    def test_thanks_query(self):
        response = self.conversation._call_ai_for_response('Hvala ti!')
        self.assertIn('Prosim', response)

    def test_recepcija_triggers_escalation(self):
        response = self.conversation._call_ai_for_response('Poveži me z recepcijo')
        self.assertEqual(self.conversation.state, 'escalated')

    def test_unknown_query_returns_helpful(self):
        response = self.conversation._call_ai_for_response('Koliko je ura?')
        self.assertTrue(len(response) > 10)


@tagged('post_install', '-at_install')
class TestAIConversationLifecycle(TransactionCase):

    def setUp(self):
        super().setUp()
        self.Config = self.env['l10n_si.ai.concierge.config']
        self.Conversation = self.env['l10n_si.ai.concierge.conversation']
        self.config = self.Config.create({'name': 'Test', 'api_key': ''})
        self.conversation = self.Conversation.create({'config_id': self.config.id})

    def test_default_state_active(self):
        self.assertEqual(self.conversation.state, 'active')

    def test_action_end(self):
        self.conversation.action_end()
        self.assertEqual(self.conversation.state, 'ended')

    def test_action_escalate(self):
        self.conversation.action_escalate()
        self.assertEqual(self.conversation.state, 'escalated')

    def test_send_message_creates_records(self):
        initial = len(self.conversation.message_ids)
        self.conversation.send_message('Test', role='user')
        self.assertEqual(len(self.conversation.message_ids), initial + 2)  # user + assistant
