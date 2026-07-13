# -*- coding: utf-8 -*-
"""Tests for AI Concierge LLM clients (ZAI, OpenAI, Anthropic, Local).

Pure unit tests — HTTP calls are mocked.
"""
import json
from unittest.mock import MagicMock, patch

from odoo.tests import TransactionCase, tagged

from odoo.addons.l10n_si_ai_concierge.models.ai_client import (
    ZAIClient, OpenAIClient, AnthropicClient, LocalLLMClient,
    PuterClient,
    get_ai_client, Message,
    AIAuthError, AIRequestError, AIRateLimitError,
)


@tagged('post_install', '-at_install')
class TestMessageModel(TransactionCase):

    def test_message_to_dict(self):
        m = Message('user', 'Hello')
        self.assertEqual(m.to_dict(), {'role': 'user', 'content': 'Hello'})


@tagged('post_install', '-at_install')
class TestAIClientFactory(TransactionCase):

    def test_factory_returns_zai(self):
        self.assertIsInstance(get_ai_client('zai', 'key', 'glm-4'), ZAIClient)

    def test_factory_returns_openai(self):
        self.assertIsInstance(get_ai_client('openai', 'key', 'gpt-4'), OpenAIClient)

    def test_factory_returns_anthropic(self):
        self.assertIsInstance(get_ai_client('anthropic', 'key', 'claude-3'), AnthropicClient)

    def test_factory_returns_local(self):
        self.assertIsInstance(get_ai_client('local', 'key', 'llama3'), LocalLLMClient)

    def test_factory_unknown_raises(self):
        from odoo.addons.l10n_si_ai_concierge.models.ai_client import AIConciergeError
        with self.assertRaises(AIConciergeError):
            get_ai_client('unknown', 'key', 'model')

    def test_local_custom_endpoint(self):
        client = get_ai_client('local', 'key', 'model', local_endpoint='http://my-llm:8080/v1/chat')
        self.assertEqual(client.endpoint, 'http://my-llm:8080/v1/chat')


@tagged('post_install', '-at_install')
class TestZAIClient(TransactionCase):

    def _mock_resp(self, code, json_data=None, text=''):
        m = MagicMock()
        m.status_code = code
        if json_data is not None:
            m.json.return_value = json_data
            m.text = json.dumps(json_data)
        else:
            m.text = text
        return m

    @patch('odoo.addons.l10n_si_ai_concierge.models.ai_client.requests.post')
    def test_successful_response(self, mock_post):
        mock_post.return_value = self._mock_resp(200, json_data={
            'choices': [{'message': {'content': 'Pozdravljen!' }}]
        })
        client = ZAIClient('key', 'glm-4-plus')
        messages = [Message('system', 'sys'), Message('user', 'hi')]
        response = client.generate_response(messages)
        self.assertEqual(response, 'Pozdravljen!')

    @patch('odoo.addons.l10n_si_ai_concierge.models.ai_client.requests.post')
    def test_auth_error(self, mock_post):
        mock_post.return_value = self._mock_resp(401, text='Unauthorized')
        with self.assertRaises(AIAuthError):
            ZAIClient('bad', 'model').generate_response([Message('user', 'x')])

    @patch('odoo.addons.l10n_si_ai_concierge.models.ai_client.requests.post')
    def test_rate_limit(self, mock_post):
        mock_post.return_value = self._mock_resp(429, text='Rate limited')
        with self.assertRaises(AIRateLimitError):
            ZAIClient('key', 'model').generate_response([Message('user', 'x')])

    @patch('odoo.addons.l10n_si_ai_concierge.models.ai_client.requests.post')
    def test_bearer_auth_header(self, mock_post):
        mock_post.return_value = self._mock_resp(200, json_data={
            'choices': [{'message': {'content': 'OK'}}]
        })
        ZAIClient('my-key', 'model').generate_response([Message('user', 'x')])
        call_args = mock_post.call_args
        self.assertEqual(call_args[1]['headers']['Authorization'], 'Bearer my-key')

    @patch('odoo.addons.l10n_si_ai_concierge.models.ai_client.requests.post')
    def test_payload_contains_model_and_messages(self, mock_post):
        mock_post.return_value = self._mock_resp(200, json_data={
            'choices': [{'message': {'content': 'OK'}}]
        })
        ZAIClient('key', 'glm-4').generate_response(
            [Message('system', 's'), Message('user', 'u')], temperature=0.5, max_tokens=100
        )
        payload = mock_post.call_args[1]['json']
        self.assertEqual(payload['model'], 'glm-4')
        self.assertEqual(len(payload['messages']), 2)
        self.assertEqual(payload['temperature'], 0.5)


@tagged('post_install', '-at_install')
class TestAnthropicClient(TransactionCase):
    """Anthropic has different format — system is top-level, not a message."""

    def _mock_resp(self, code, json_data=None, text=''):
        m = MagicMock()
        m.status_code = code
        if json_data is not None:
            m.json.return_value = json_data
            m.text = json.dumps(json_data)
        else:
            m.text = text
        return m

    @patch('odoo.addons.l10n_si_ai_concierge.models.ai_client.requests.post')
    def test_system_extracted_to_top_level(self, mock_post):
        mock_post.return_value = self._mock_resp(200, json_data={
            'content': [{'text': 'Hello from Claude'}]
        })
        client = AnthropicClient('key', 'claude-3')
        messages = [Message('system', 'You are helpful.'), Message('user', 'hi')]
        client.generate_response(messages)
        payload = mock_post.call_args[1]['json']
        self.assertEqual(payload['system'], 'You are helpful.')
        for msg in payload['messages']:
            self.assertNotEqual(msg['role'], 'system')

    @patch('odoo.addons.l10n_si_ai_concierge.models.ai_client.requests.post')
    def test_x_api_key_header(self, mock_post):
        """Anthropic uses x-api-key, not Authorization Bearer."""
        mock_post.return_value = self._mock_resp(200, json_data={
            'content': [{'text': 'OK'}]
        })
        AnthropicClient('my-key', 'claude-3').generate_response([Message('user', 'hi')])
        headers = mock_post.call_args[1]['headers']
        self.assertEqual(headers['x-api-key'], 'my-key')
        self.assertNotIn('Authorization', headers)


@tagged('post_install', '-at_install')
class TestLocalLLMClient(TransactionCase):

    def _mock_resp(self, code, json_data=None, text=''):
        m = MagicMock()
        m.status_code = code
        if json_data is not None:
            m.json.return_value = json_data
            m.text = json.dumps(json_data)
        else:
            m.text = text
        return m

    @patch('odoo.addons.l10n_si_ai_concierge.models.ai_client.requests.post')
    def test_custom_endpoint_used(self, mock_post):
        mock_post.return_value = self._mock_resp(200, json_data={
            'choices': [{'message': {'content': 'OK'}}]
        })
        client = LocalLLMClient('key', 'llama3', endpoint='http://my-server:8080/v1/chat')
        client.generate_response([Message('user', 'hi')])
        self.assertEqual(mock_post.call_args[0][0], 'http://my-server:8080/v1/chat')

    @patch('odoo.addons.l10n_si_ai_concierge.models.ai_client.requests.post')
    def test_no_auth_header_without_key(self, mock_post):
        mock_post.return_value = self._mock_resp(200, json_data={
            'choices': [{'message': {'content': 'OK'}}]
        })
        LocalLLMClient('', 'llama3').generate_response([Message('user', 'hi')])
        self.assertNotIn('Authorization', mock_post.call_args[1]['headers'])

    @patch('odoo.addons.l10n_si_ai_concierge.models.ai_client.requests.post')
    def test_auth_header_with_key(self, mock_post):
        mock_post.return_value = self._mock_resp(200, json_data={
            'choices': [{'message': {'content': 'OK'}}]
        })
        LocalLLMClient('secret', 'llama3').generate_response([Message('user', 'hi')])
        self.assertEqual(mock_post.call_args[1]['headers']['Authorization'], 'Bearer secret')


@tagged('post_install', '-at_install')
class TestPuterClient(TransactionCase):
    """Tests for Puter.com free AI API client."""

    def _mock_resp(self, code, json_data=None, text=''):
        m = MagicMock()
        m.status_code = code
        if json_data is not None:
            m.json.return_value = json_data
            m.text = json.dumps(json_data)
        else:
            m.text = text
        return m

    def test_factory_returns_puter(self):
        """get_ai_client should return PuterClient for 'puter' backend."""
        client = get_ai_client('puter', 'puter-token', 'z-ai/glm-5.1')
        self.assertIsInstance(client, PuterClient)

    def test_puter_uses_correct_endpoint(self):
        """PuterClient should use the Puter.com API endpoint."""
        client = PuterClient('token', 'z-ai/glm-5.1')
        self.assertIn('api.puter.com', client.endpoint)
        self.assertIn('puterai', client.endpoint)

    @patch('odoo.addons.l10n_si_ai_concierge.models.ai_client.requests.post')
    def test_successful_response(self, mock_post):
        """PuterClient should parse OpenAI-format response correctly."""
        mock_post.return_value = self._mock_resp(200, json_data={
            'choices': [{'message': {'content': 'Pozdravljen iz Puterja!'}}]
        })
        client = PuterClient('puter-token', 'z-ai/glm-5.1')
        response = client.generate_response([Message('user', 'hi')])
        self.assertEqual(response, 'Pozdravljen iz Puterja!')

    @patch('odoo.addons.l10n_si_ai_concierge.models.ai_client.requests.post')
    def test_auth_error(self, mock_post):
        """Invalid Puter token should raise AIAuthError."""
        mock_post.return_value = self._mock_resp(401, text='Unauthorized')
        with self.assertRaises(AIAuthError):
            PuterClient('bad-token', 'z-ai/glm-5.1').generate_response(
                [Message('user', 'x')]
            )

    @patch('odoo.addons.l10n_si_ai_concierge.models.ai_client.requests.post')
    def test_rate_limit(self, mock_post):
        """Rate limit (429) should raise AIRateLimitError."""
        mock_post.return_value = self._mock_resp(429, text='Rate limited')
        with self.assertRaises(AIRateLimitError):
            PuterClient('token', 'z-ai/glm-5.1').generate_response(
                [Message('user', 'x')]
            )

    @patch('odoo.addons.l10n_si_ai_concierge.models.ai_client.requests.post')
    def test_bearer_auth_header(self, mock_post):
        """PuterClient should use Bearer auth with the provided token."""
        mock_post.return_value = self._mock_resp(200, json_data={
            'choices': [{'message': {'content': 'OK'}}]
        })
        PuterClient('my-puter-token', 'z-ai/glm-5.1').generate_response(
            [Message('user', 'x')]
        )
        headers = mock_post.call_args[1]['headers']
        self.assertEqual(headers['Authorization'], 'Bearer my-puter-token')

    @patch('odoo.addons.l10n_si_ai_concierge.models.ai_client.requests.post')
    def test_payload_contains_model_and_messages(self, mock_post):
        """Payload should include the model name and messages array."""
        mock_post.return_value = self._mock_resp(200, json_data={
            'choices': [{'message': {'content': 'OK'}}]
        })
        PuterClient('token', 'z-ai/glm-5.1').generate_response(
            [Message('system', 's'), Message('user', 'u')],
            temperature=0.5, max_tokens=100
        )
        payload = mock_post.call_args[1]['json']
        self.assertEqual(payload['model'], 'z-ai/glm-5.1')
        self.assertEqual(len(payload['messages']), 2)
        self.assertEqual(payload['temperature'], 0.5)
        self.assertEqual(payload['max_tokens'], 100)

    @patch('odoo.addons.l10n_si_ai_concierge.models.ai_client.requests.post')
    def test_server_error(self, mock_post):
        """Server errors (5xx) should raise AIRequestError."""
        mock_post.return_value = self._mock_resp(502, text='Bad Gateway')
        with self.assertRaises(AIRequestError):
            PuterClient('token', 'z-ai/glm-5.1').generate_response(
                [Message('user', 'x')]
            )
