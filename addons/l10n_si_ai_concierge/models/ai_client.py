# -*- coding: utf-8 -*-
"""AI LLM client for SI AI Concierge.

Wraps multiple LLM backends (ZAI, OpenAI, Anthropic, Local) behind a single interface.
"""
import json
import logging
from typing import List, Optional

import requests

_logger = logging.getLogger(__name__)

DEFAULT_TIMEOUT = 30
ZAI_ENDPOINT = 'https://internal-api.z.ai/v1/chat/completions'
OPENAI_ENDPOINT = 'https://api.openai.com/v1/chat/completions'
ANTHROPIC_ENDPOINT = 'https://api.anthropic.com/v1/messages'


class AIConciergeError(Exception): pass
class AIAuthError(AIConciergeError): pass
class AIRequestError(AIConciergeError): pass
class AIRateLimitError(AIConciergeError): pass


class Message:
    def __init__(self, role: str, content: str):
        self.role = role
        self.content = content
    def to_dict(self) -> dict:
        return {'role': self.role, 'content': self.content}


class AIClient:
    def __init__(self, api_key: str, model: str, timeout: int = DEFAULT_TIMEOUT):
        self.api_key = api_key
        self.model = model
        self.timeout = timeout
    def generate_response(self, messages: List[Message], temperature: float = 0.7, max_tokens: int = 500) -> str:
        raise NotImplementedError()


class ZAIClient(AIClient):
    def generate_response(self, messages, temperature=0.7, max_tokens=500):
        payload = {'model': self.model, 'messages': [m.to_dict() for m in messages],
                   'temperature': temperature, 'max_tokens': max_tokens,
                   'thinking': {'type': 'disabled'}}
        headers = {'Authorization': f'Bearer {self.api_key}', 'Content-Type': 'application/json',
                   'X-Z-AI-From': 'Z'}
        if len(self.api_key) > 100 and '.' in self.api_key:
            headers['X-Token'] = self.api_key
            headers['Authorization'] = 'Bearer Z.ai'
        try:
            response = requests.post(ZAI_ENDPOINT, headers=headers, json=payload, timeout=self.timeout)
        except requests.Timeout as e: raise AIRequestError(f'ZAI timeout: {e}') from e
        except requests.RequestException as e: raise AIRequestError(f'ZAI network error: {e}') from e
        if response.status_code == 401: raise AIAuthError('Invalid ZAI API key')
        if response.status_code == 429: raise AIRateLimitError('ZAI rate limit exceeded')
        if response.status_code >= 500: raise AIRequestError(f'ZAI server error {response.status_code}')
        if response.status_code != 200: raise AIRequestError(f'ZAI HTTP {response.status_code}: {response.text[:300]}')
        try: return response.json()['choices'][0]['message']['content'].strip()
        except (ValueError, KeyError, IndexError) as e: raise AIRequestError(f'Invalid ZAI response: {e}') from e


class OpenAIClient(AIClient):
    def generate_response(self, messages, temperature=0.7, max_tokens=500):
        payload = {'model': self.model, 'messages': [m.to_dict() for m in messages],
                   'temperature': temperature, 'max_tokens': max_tokens}
        headers = {'Authorization': f'Bearer {self.api_key}', 'Content-Type': 'application/json'}
        try:
            response = requests.post(OPENAI_ENDPOINT, headers=headers, json=payload, timeout=self.timeout)
        except requests.Timeout as e: raise AIRequestError(f'OpenAI timeout: {e}') from e
        except requests.RequestException as e: raise AIRequestError(f'OpenAI network error: {e}') from e
        if response.status_code == 401: raise AIAuthError('Invalid OpenAI API key')
        if response.status_code == 429: raise AIRateLimitError('OpenAI rate limit exceeded')
        if response.status_code >= 500: raise AIRequestError(f'OpenAI server error {response.status_code}')
        if response.status_code != 200: raise AIRequestError(f'OpenAI HTTP {response.status_code}')
        try: return response.json()['choices'][0]['message']['content'].strip()
        except (ValueError, KeyError, IndexError) as e: raise AIRequestError(f'Invalid OpenAI response: {e}') from e


class AnthropicClient(AIClient):
    def generate_response(self, messages, temperature=0.7, max_tokens=500):
        system_content = ''
        chat_messages = []
        for m in messages:
            if m.role == 'system': system_content = m.content
            else: chat_messages.append(m.to_dict())
        payload = {'model': self.model, 'system': system_content, 'messages': chat_messages,
                   'temperature': temperature, 'max_tokens': max_tokens}
        headers = {'x-api-key': self.api_key, 'anthropic-version': '2023-06-01', 'Content-Type': 'application/json'}
        try:
            response = requests.post(ANTHROPIC_ENDPOINT, headers=headers, json=payload, timeout=self.timeout)
        except requests.Timeout as e: raise AIRequestError(f'Anthropic timeout: {e}') from e
        except requests.RequestException as e: raise AIRequestError(f'Anthropic network error: {e}') from e
        if response.status_code == 401: raise AIAuthError('Invalid Anthropic API key')
        if response.status_code == 429: raise AIRateLimitError('Anthropic rate limit exceeded')
        if response.status_code >= 500: raise AIRequestError(f'Anthropic server error {response.status_code}')
        if response.status_code != 200: raise AIRequestError(f'Anthropic HTTP {response.status_code}')
        try: return response.json()['content'][0]['text'].strip()
        except (ValueError, KeyError, IndexError) as e: raise AIRequestError(f'Invalid Anthropic response: {e}') from e


class LocalLLMClient(AIClient):
    def __init__(self, api_key, model, timeout=DEFAULT_TIMEOUT, endpoint='http://localhost:11434/v1/chat/completions'):
        super().__init__(api_key, model, timeout)
        self.endpoint = endpoint
    def generate_response(self, messages, temperature=0.7, max_tokens=500):
        payload = {'model': self.model, 'messages': [m.to_dict() for m in messages],
                   'temperature': temperature, 'max_tokens': max_tokens}
        headers = {'Content-Type': 'application/json'}
        if self.api_key: headers['Authorization'] = f'Bearer {self.api_key}'
        try:
            response = requests.post(self.endpoint, headers=headers, json=payload, timeout=self.timeout)
        except requests.RequestException as e: raise AIRequestError(f'Local LLM error: {e}') from e
        if response.status_code != 200: raise AIRequestError(f'Local LLM HTTP {response.status_code}')
        try: return response.json()['choices'][0]['message']['content'].strip()
        except (ValueError, KeyError, IndexError) as e: raise AIRequestError(f'Invalid local LLM response: {e}') from e


class OpenAICompatibleClient(AIClient):
    """Generic OpenAI-compatible client for gateway services (ZenMux, Together, Anyscale, OpenRouter, etc.).

    Many LLM gateway services expose an OpenAI-compatible /v1/chat/completions endpoint.
    Instead of hardcoding each gateway, we accept a custom endpoint URL and reuse the
    OpenAI request/response format.
    """
    def __init__(self, api_key, model, timeout=DEFAULT_TIMEOUT, endpoint=None):
        super().__init__(api_key, model, timeout)
        if not endpoint:
            raise AIConciergeError('OpenAI-compatible backend requires endpoint URL')
        # Parse extra headers from endpoint URL format: URL|Header:Value|Header2:Value2
        self._extra_headers = {}
        if '|' in endpoint:
            parts = endpoint.split('|')
            endpoint = parts[0]
            for part in parts[1:]:
                if ':' in part:
                    h_name, h_value = part.split(':', 1)
                    self._extra_headers[h_name.strip()] = h_value.strip()
        # Also add X-Z-AI-From header for Z.AI compatibility
        if 'internal-api.z.ai' in endpoint:
            self._extra_headers['X-Z-AI-From'] = 'Z'
        # Normalize: strip trailing slash, ensure ends with /v1/chat/completions
        endpoint = endpoint.rstrip('/')
        if not endpoint.endswith('/v1/chat/completions'):
            if endpoint.endswith('/v1'):
                endpoint = endpoint + '/chat/completions'
            elif '/v1/' not in endpoint and not endpoint.endswith('/v1'):
                endpoint = endpoint + '/v1/chat/completions'
            else:
                endpoint = endpoint + '/chat/completions'
        self.endpoint = endpoint

    def generate_response(self, messages, temperature=0.7, max_tokens=500):
        payload = {'model': self.model, 'messages': [m.to_dict() for m in messages],
                   'temperature': temperature, 'max_tokens': max_tokens}
        headers = {'Authorization': f'Bearer {self.api_key}', 'Content-Type': 'application/json'}
        # Support custom headers via endpoint_url format: URL|Header:Value
        # e.g. https://internal-api.z.ai/v1|X-Token:eyJhbGc...
        if hasattr(self, '_extra_headers'):
            headers.update(self._extra_headers)
        try:
            response = requests.post(self.endpoint, headers=headers, json=payload, timeout=self.timeout)
        except requests.Timeout as e: raise AIRequestError(f'OpenAI-compat timeout: {e}') from e
        except requests.RequestException as e: raise AIRequestError(f'OpenAI-compat network error: {e}') from e
        if response.status_code == 401: raise AIAuthError('Invalid API key for OpenAI-compatible endpoint')
        if response.status_code == 403: raise AIAuthError(f'Access denied (403). Check subscription/balance on gateway dashboard: {response.text[:300]}')
        if response.status_code == 429: raise AIRateLimitError('Rate limit exceeded on OpenAI-compatible endpoint')
        if response.status_code >= 500: raise AIRequestError(f'OpenAI-compat server error {response.status_code}')
        if response.status_code != 200: raise AIRequestError(f'OpenAI-compat HTTP {response.status_code}: {response.text[:300]}')
        try: return response.json()['choices'][0]['message']['content'].strip()
        except (ValueError, KeyError, IndexError) as e: raise AIRequestError(f'Invalid OpenAI-compat response: {e}') from e


def get_ai_client(backend, api_key, model, timeout=DEFAULT_TIMEOUT, local_endpoint=None, endpoint_url=None):
    if backend == 'zai': return ZAIClient(api_key, model, timeout)
    elif backend == 'openai': return OpenAIClient(api_key, model, timeout)
    elif backend == 'anthropic': return AnthropicClient(api_key, model, timeout)
    elif backend == 'local': return LocalLLMClient(api_key, model, timeout, local_endpoint or 'http://localhost:11434/v1/chat/completions')
    elif backend in ('openai_compatible', 'zenmux'): return OpenAICompatibleClient(api_key, model, timeout, endpoint_url)
    elif backend == 'puter': return PuterClient(api_key, model, timeout)
    else: raise AIConciergeError(f'Unknown AI backend: {backend}')


class PuterClient(OpenAICompatibleClient):
    """Puter.com free AI API client.

    Puter provides free access to multiple AI models including:
    - z-ai/glm-5.1 (Z.AI GLM 5.1 — newer than GLM 4 Plus)
    - z-ai/glm-4.1 (Z.AI GLM 4.1)
    - openai/gpt-4o (OpenAI GPT-4o)
    - anthropic/claude-3-5-sonnet (Anthropic Claude)
    - and many more

    Endpoint: https://api.puter.com/puterai/openai/v1/chat/completions
    Auth: Bearer token (Puter auth token from puter.com)

    Usage:
        client = PuterClient('your-puter-token', 'z-ai/glm-5.1')
        response = client.generate_response([Message('user', 'Hello!')])

    Note: Puter API is free but rate-limited. For production use with
    high traffic, consider Z.AI direct API or OpenAI.
    """
    PUTER_ENDPOINT = 'https://api.puter.com/puterai/openai/v1/chat/completions'

    def __init__(self, api_key, model, timeout=DEFAULT_TIMEOUT):
        # Initialize parent with Puter endpoint
        super().__init__(api_key, model, timeout, self.PUTER_ENDPOINT)

    def generate_response(self, messages, temperature=0.7, max_tokens=1000):
        """Override to add Puter-specific handling.

        Puter API accepts standard OpenAI format but:
        - Does not support 'thinking' parameter (unlike Z.AI direct)
        - Some models may not support 'temperature' (ignored gracefully)
        - GLM 5.1 uses many tokens for internal reasoning (800+), so
          default max_tokens is 1000 (was 500) to avoid empty responses.
        """
        payload = {
            'model': self.model,
            'messages': [m.to_dict() for m in messages],
            'temperature': temperature,
            'max_tokens': max_tokens,
        }
        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json',
        }
        try:
            import requests as req
            response = req.post(self.endpoint, headers=headers, json=payload, timeout=self.timeout)
        except req.Timeout as e:
            raise AIRequestError(f'Puter timeout: {e}') from e
        except req.RequestException as e:
            raise AIRequestError(f'Puter network error: {e}') from e

        if response.status_code == 401:
            raise AIAuthError('Invalid Puter auth token')
        if response.status_code == 429:
            raise AIRateLimitError('Puter rate limit exceeded (free tier)')
        if response.status_code >= 500:
            raise AIRequestError(f'Puter server error {response.status_code}')
        if response.status_code != 200:
            raise AIRequestError(f'Puter HTTP {response.status_code}: {response.text[:300]}')

        try:
            return response.json()['choices'][0]['message']['content'].strip()
        except (ValueError, KeyError, IndexError) as e:
            raise AIRequestError(f'Invalid Puter response: {e}') from e
