# -*- coding: utf-8 -*-
"""Chatbot widget controller — AJAX endpoint za AI odgovore."""
import logging
from odoo import http
from odoo.http import request
from odoo.exceptions import AccessDenied

_logger = logging.getLogger(__name__)

# Default rate limit: 10 requests per minute per IP
DEFAULT_RATE_LIMIT = 10
DEFAULT_RATE_WINDOW = 60


def _check_rate_limit(endpoint):
    """Check rate limit for the current request."""
    RateLimitLog = request.env.get('l10n_si.rate.limit.log')
    if not RateLimitLog:
        return (True, -1)

    ip = RateLimitLog.get_client_ip(request)

    RateLimitConfig = request.env.get('l10n_si.rate.limit.config')
    if RateLimitConfig:
        config = RateLimitConfig.sudo().get_config_for_endpoint(endpoint)
        if config:
            if ip in config['whitelisted_ips']:
                return (True, -1)
            max_req = config['max_requests']
            window = config['window_seconds']
        else:
            max_req = DEFAULT_RATE_LIMIT
            window = DEFAULT_RATE_WINDOW
    else:
        max_req = DEFAULT_RATE_LIMIT
        window = DEFAULT_RATE_WINDOW

    allowed, remaining, retry_after = RateLimitLog.sudo().check_rate_limit(
        endpoint, ip, max_req, window
    )
    if not allowed:
        _logger.warning('Rate limit exceeded for %s on %s', ip, endpoint)
        raise AccessDenied('Rate limit exceeded')
    return (allowed, remaining)


class ChatbotController(http.Controller):
    @http.route('/chatbot/send', type='json', auth='public', website=True)
    def send_message(self, **kwargs):
        """Prejme sporočilo od spletnega widgeta, vrne AI odgovor."""
        # Rate limiting
        try:
            _check_rate_limit('/chatbot/send')
        except AccessDenied:
            return {'error': 'Preveč sporočil. Poskusite kasneje.',
                    'error_en': 'Too many requests. Please try again later.'}

        # Extract message from JSON body
        data = request.get_json_data() or {}
        message = data.get('message', '') if isinstance(data, dict) else ''
        if not message:
            message = kwargs.get('message', '')

        if not message or len(message) > 1000:
            return {'error': 'Sporočilo je predolgo ali prazno.'}
        
        # Poišči aktivno AI konfiguracijo
        Config = request.env['l10n_si.ai.concierge.config']
        config = Config.sudo().search([('active', '=', True), ('enabled_website', '=', True)], limit=1)
        
        if not config:
            return {'error': 'AI asistent trenutno ni na voljo.'}
        
        # Ustvari ali poišči pogovor
        Conversation = request.env['l10n_si.ai.concierge.conversation']
        partner = request.env.user.partner_id if request.env.user.partner_id != request.env.ref('base.public_partner') else False
        
        conv_vals = {
            'name': f'Website chat - {message[:30]}',
            'config_id': config.id,
            'channel': 'website',
        }
        if partner:
            conv_vals['partner_id'] = partner.id
        
        conv = Conversation.sudo().create(conv_vals)
        
        # Pošlji sporočilo in pridobi AI odgovor
        try:
            response = conv.sudo().send_message(message)
            return {
                'success': True,
                'response': response or 'Oprostite, trenutno ne morem odgovoriti.',
                'conversation_id': conv.id,
            }
        except Exception as e:
            _logger.error('Chatbot error: %s', e)
            return {'error': 'Prišlo je do napake. Poskusite kasneje.'}
    
    @http.route('/chatbot/history', type='json', auth='public', website=True)
    def get_history(self, **kwargs):
        """Vrni zgodovino pogovora."""
        data = request.get_json_data() or {}
        conversation_id = data.get('conversation_id') if isinstance(data, dict) else None
        if not conversation_id:
            conversation_id = kwargs.get('conversation_id')
        if not conversation_id:
            return {'messages': []}
        
        conv = request.env['l10n_si.ai.concierge.conversation'].sudo().browse(conversation_id)
        if not conv.exists():
            return {'messages': []}
        
        messages = []
        for msg in conv.message_ids:
            messages.append({
                'role': msg.role,
                'content': msg.content,
                'time': msg.create_date.strftime('%H:%M') if msg.create_date else '',
            })
        return {'messages': messages}
