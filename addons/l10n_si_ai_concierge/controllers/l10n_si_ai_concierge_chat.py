# -*- coding: utf-8 -*-
"""Webchat endpoint for guests."""
import json
import logging

from odoo import http
from odoo.http import request
from odoo.exceptions import AccessDenied

_logger = logging.getLogger(__name__)

# Default rate limit: 10 requests per minute per IP
DEFAULT_RATE_LIMIT = 10
DEFAULT_RATE_WINDOW = 60  # seconds


def _check_rate_limit(endpoint):
    """Check rate limit for the current request.

    Raises AccessDenied if rate limit exceeded.
    Returns (allowed, remaining) tuple.
    """
    RateLimitLog = request.env.get('l10n_si.rate.limit.log')
    if not RateLimitLog:
        # Rate limit module not installed — allow
        return (True, -1)

    ip = RateLimitLog.get_client_ip(request)

    # Check if config exists for this endpoint
    RateLimitConfig = request.env.get('l10n_si.rate.limit.config')
    if RateLimitConfig:
        config = RateLimitConfig.sudo().get_config_for_endpoint(endpoint)
        if config:
            if ip in config['whitelisted_ips']:
                return (True, -1)
            max_req = config['max_requests']
            window = config['window_seconds']
        else:
            # No config — use defaults
            max_req = DEFAULT_RATE_LIMIT
            window = DEFAULT_RATE_WINDOW
    else:
        max_req = DEFAULT_RATE_LIMIT
        window = DEFAULT_RATE_WINDOW

    allowed, remaining, retry_after = RateLimitLog.sudo().check_rate_limit(
        endpoint, ip, max_req, window
    )
    if not allowed:
        _logger.warning('Rate limit exceeded for %s on %s (retry after %ds)',
                        ip, endpoint, retry_after)
        raise AccessDenied(
            f'Rate limit exceeded. Retry after {retry_after} seconds.'
        )
    return (allowed, remaining)


class L10nSiAiConciergeChat(http.Controller):
    """Public webchat endpoint for guests."""

    @http.route('/ai-concierge/chat', type='json', auth='public', methods=['POST'], csrf=False)
    def chat(self, **kwargs):
        """Receive a guest message and return AI response."""
        # Rate limiting
        try:
            _check_rate_limit('/ai-concierge/chat')
        except AccessDenied:
            return json.dumps({'error': 'Rate limit exceeded', 'retry_after': 60})

        try:
            data = request.get_json_data()
            message = data.get('message', '').strip()
            conversation_id = data.get('conversation_id')

            if not message:
                return json.dumps({'error': 'Empty message'})

            cfg = request.env['l10n_si.ai.concierge.config'].sudo().search([
                ('active', '=', True),
            ], limit=1)
            if not cfg:
                return json.dumps({'error': 'AI Concierge not configured'})

            # Najdi ali ustvari pogovor
            conversation = False
            if conversation_id:
                conversation = request.env['l10n_si.ai.concierge.conversation'].sudo().browse(conversation_id)
            if not conversation or not conversation.exists():
                # Najdi partnerja po e-pošti ali ustvari novega
                partner = False
                if data.get('guest_email'):
                    partner = request.env['res.partner'].sudo().search([
                        ('email', '=', data.get('guest_email')),
                    ], limit=1)
                conversation = request.env['l10n_si.ai.concierge.conversation'].sudo().create({
                    'config_id': cfg.id,
                    'partner_id': partner.id if partner else False,
                    'channel': 'website',
                })

            # Pošlji sporočilo in pridobi AI odgovor
            ai_response = conversation.sudo().send_message(message, role='user')

            return json.dumps({
                'conversation_id': conversation.id,
                'response': ai_response,
            })
        except Exception as e:
            _logger.exception('AI Concierge chat error: %s', e)
            return json.dumps({'error': str(e)})

    @http.route('/ai-concierge/history/<int:conversation_id>', type='json', auth='public')
    def history(self, conversation_id, **kwargs):
        """Get conversation history."""
        conv = request.env['l10n_si.ai.concierge.conversation'].sudo().browse(conversation_id)
        if not conv.exists():
            return json.dumps({'error': 'Conversation not found'})
        messages = []
        for msg in conv.message_ids:
            messages.append({
                'role': msg.role,
                'content': msg.content,
                'timestamp': msg.create_date.isoformat() if msg.create_date else None,
            })
        return json.dumps({
            'conversation_id': conv.id,
            'state': conv.state,
            'messages': messages,
        })
