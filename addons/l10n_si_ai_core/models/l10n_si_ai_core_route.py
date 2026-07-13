# -*- coding: utf-8 -*-
"""AI Core Route — task-based routing configuration.

Maps task types to providers. When a module requests AI generation,
it specifies a task_type, and the router finds the best provider.
"""
import logging

from odoo import api, fields, models

from odoo.addons.l10n_si_ai_concierge.models.ai_client import (
    get_ai_client, Message,
    AIAuthError, AIRequestError, AIRateLimitError,
)

_logger = logging.getLogger(__name__)


class L10nSiAiCoreRoute(models.Model):
    _name = 'l10n_si.ai.core.route'
    _description = 'AI Core Router'
    _order = 'task_type, priority'

    def _default_system_prompt(self):
        return "Si prijazen AI asistent. Odgovarjaj jedrnato in prijazno."

    name = fields.Char(
        string='Ime', required=True,
        compute='_compute_name', store=True,
    )
    task_type = fields.Selection(
        selection=[
            ('general', 'Splošno'),
            ('simple', 'Preprosto (hitri odgovori)'),
            ('reasoning', 'Kompleksno (razmišljanje)'),
            ('creative', 'Kreativno (marketing)'),
            ('multilingual', 'Večjezično (SI/HR/EN)'),
        ],
        default='general',
        required=True,
    )
    system_prompt = fields.Text(
        string='Sistemski prompt', default=_default_system_prompt,
        help='Override sistemskega prompta za to nalogo. Prazno = uporabi config.',
    )
    temperature = fields.Float(
        string='Temperature (kreativnost)', default=0.7,
        help='0 = deterministično, 1 = zelo kreativno',
    )
    max_tokens = fields.Integer(
        string='Max tokeni', default=1000,
        help='GLM 5.1 potrebuje 1000+, GPT-4o dovolj 500',
    )
    active = fields.Boolean(string='Aktiven', default=True)
    company_id = fields.Many2one(
        'res.company', string='Company',
        default=lambda self: self.env.company, required=True,
    )

    _sql_constraints = [
        ('task_type_company_unique',
         'unique(task_type, company_id)',
         'Route za ta task_type že obstaja!'),
    ]

    @api.depends('task_type', 'system_prompt')
    def _compute_name(self):
        for r in self:
            r.name = f'AI Route: {r.task_type}'

    @api.model
    def get_providers_for_task(self, task_type='general'):
        """Get active providers for a task type, ordered by priority.

        Falls back to 'general' task_type if no specific providers found.
        Returns list of provider records (empty if none).
        """
        # Try task-specific providers first
        providers = self.env['l10n_si.ai.core.provider'].search([
            ('task_type', '=', task_type),
            ('active', '=', True),
            ('company_id', 'in', [self.env.company.id, False]),
        ], order='priority')

        if not providers and task_type != 'general':
            # Fallback to general providers
            providers = self.env['l10n_si.ai.core.provider'].search([
                ('task_type', '=', 'general'),
                ('active', '=', True),
                ('company_id', 'in', [self.env.company.id, False]),
            ], order='priority')

        return providers

    @api.model
    def generate(self, messages, task_type='general', system_prompt=None,
                 temperature=None, max_tokens=None, source_module='unknown'):
        """Generate AI response with automatic fallback.

        Args:
            messages: List of Message objects or list of dicts
                [{'role': 'user', 'content': 'Hello'}]
            task_type: Type of task (determines provider selection)
            system_prompt: Override system prompt
            temperature: Override temperature (0-1)
            max_tokens: Override max tokens
            source_module: Name of calling module (for tracking)

        Returns:
            dict with keys:
                - 'response': str (AI response text)
                - 'provider': str (backend that succeeded)
                - 'model': str (model name)
                - 'attempts': list of dicts (all providers tried)
                - 'success': bool

        Raises:
            UserError if all providers fail
        """
        # Get route config for this task
        route = self.search([
            ('task_type', '=', task_type),
            ('active', '=', True),
            ('company_id', 'in', [self.env.company.id, False]),
        ], limit=1)

        # Apply route defaults
        if system_prompt is None:
            system_prompt = route.system_prompt if route else \
                "Si prijazen AI asistent. Odgovarjaj jedrnato in prijazno."
        if temperature is None:
            temperature = route.temperature if route else 0.7
        if max_tokens is None:
            max_tokens = route.max_tokens if route else 1000

        # Convert dict messages to Message objects
        normalized_messages = []
        for msg in messages:
            if isinstance(msg, Message):
                normalized_messages.append(msg)
            elif isinstance(msg, dict):
                normalized_messages.append(
                    Message(msg.get('role', 'user'), msg.get('content', ''))
                )

        # Prepend system prompt
        if system_prompt:
            normalized_messages.insert(0, Message('system', system_prompt))

        # Get providers
        providers = self.get_providers_for_task(task_type)
        if not providers:
            _logger.warning('AI Core: no providers for task_type=%s', task_type)
            return {
                'response': '',
                'provider': 'none',
                'model': 'none',
                'attempts': [],
                'success': False,
                'error': f'No AI providers configured for task: {task_type}',
            }

        # Try each provider in priority order (fallback chain)
        attempts = []
        for provider in providers:
            cfg = provider.config_id
            if not cfg.api_key:
                _logger.debug('AI Core: skipping %s (no API key)', provider.name)
                continue

            # Use provider's max_tokens_override if set
            effective_max_tokens = provider.max_tokens_override or max_tokens

            attempt = {
                'provider': cfg.ai_backend,
                'model': cfg.model_name,
                'max_tokens': effective_max_tokens,
            }

            try:
                client = get_ai_client(
                    backend=cfg.ai_backend,
                    api_key=cfg.api_key,
                    model=cfg.model_name,
                    endpoint_url=cfg.endpoint_url,
                )
                response = client.generate_response(
                    messages=normalized_messages,
                    temperature=temperature,
                    max_tokens=effective_max_tokens,
                )

                attempt['success'] = True
                attempt['response'] = response
                attempts.append(attempt)

                # Track usage
                self.env['l10n_si.ai.core.usage'].log_usage(
                    source_module=source_module,
                    task_type=task_type,
                    provider=cfg.ai_backend,
                    model=cfg.model_name,
                    success=True,
                )

                return {
                    'response': response,
                    'provider': cfg.ai_backend,
                    'model': cfg.model_name,
                    'attempts': attempts,
                    'success': True,
                }

            except (AIAuthError, AIRateLimitError, AIRequestError) as e:
                attempt['success'] = False
                attempt['error'] = str(e)
                attempts.append(attempt)
                _logger.warning(
                    'AI Core: provider %s/%s failed (%s) — trying next',
                    cfg.ai_backend, cfg.model_name, type(e).__name__
                )
                # Track failed attempt
                self.env['l10n_si.ai.core.usage'].log_usage(
                    source_module=source_module,
                    task_type=task_type,
                    provider=cfg.ai_backend,
                    model=cfg.model_name,
                    success=False,
                    error=str(e)[:500],
                )
                continue

            except Exception as e:
                attempt['success'] = False
                attempt['error'] = str(e)
                attempts.append(attempt)
                _logger.exception(
                    'AI Core: unexpected error with %s: %s',
                    cfg.ai_backend, e
                )
                continue

        # All providers failed
        _logger.error('AI Core: all providers failed for task %s', task_type)
        return {
            'response': '',
            'provider': 'none',
            'model': 'none',
            'attempts': attempts,
            'success': False,
            'error': 'All AI providers failed. Check provider configurations.',
        }
