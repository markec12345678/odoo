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
ZAI_ENDPOINT = 'https://open.bigmodel.cn/api/paas/v4/chat/completions'
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
                   'temperature': temperature, 'max_tokens': max_tokens}
        headers = {'Authorization': f'Bearer {self.api_key}', 'Content-Type': 'application/json'}
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


def get_ai_client(backend, api_key, model, timeout=DEFAULT_TIMEOUT, local_endpoint=None):
    if backend == 'zai': return ZAIClient(api_key, model, timeout)
    elif backend == 'openai': return OpenAIClient(api_key, model, timeout)
    elif backend == 'anthropic': return AnthropicClient(api_key, model, timeout)
    elif backend == 'local': return LocalLLMClient(api_key, model, timeout, local_endpoint or 'http://localhost:11434/v1/chat/completions')
    else: raise AIConciergeError(f'Unknown AI backend: {backend}')
