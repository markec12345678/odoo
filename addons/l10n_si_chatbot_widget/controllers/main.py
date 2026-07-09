import json
import logging
from odoo import http
from odoo.http import request

_logger = logging.getLogger(__name__)


class ChatbotController(http.Controller):
    @http.route('/chatbot/send', type='json', auth='public', website=True)
    def send_message(self, message, **kw):
        """Receive a message from the website widget and get AI response."""
        if not message or len(message) > 1000:
            return {'error': 'Invalid message'}

        # Find active AI config
        config = request.env['l10n_si.ai.concierge.config'].sudo().search([
            ('active', '=', True),
            ('enabled_website', '=', True),
        ], limit=1)

        if not config:
            return {'error': 'AI Concierge not configured'}

        # Create or find conversation for this session
        session_id = request.session.sid
        conv = request.env['l10n_si.ai.concierge.conversation'].sudo().search([
            ('name', '=', f'Web-{session_id}'),
            ('config_id', '=', config.id),
        ], limit=1)

        if not conv:
            conv = request.env['l10n_si.ai.concierge.conversation'].sudo().create({
                'name': f'Web-{session_id}',
                'config_id': config.id,
                'channel': 'website',
            })

        # Send message and get AI response
        try:
            response = conv.send_message(message)
            return {'response': response or 'Oprostite, trenutno ne morem odgovoriti. Kontaktirajte recepcijo.'}
        except Exception as e:
            _logger.error('Chatbot error: %s', e)
            return {'error': 'Something went wrong. Please try again.'}

    @http.route('/chatbot/history', type='json', auth='public', website=True)
    def get_history(self, **kw):
        """Get conversation history for current session."""
        session_id = request.session.sid
        conv = request.env['l10n_si.ai.concierge.conversation'].sudo().search([
            ('name', '=', f'Web-{session_id}'),
        ], limit=1)

        if not conv:
            return {'messages': []}

        messages = []
        for msg in conv.message_ids:
            messages.append({
                'role': msg.role,
                'content': msg.content,
                'time': msg.create_date.strftime('%H:%M') if msg.create_date else '',
            })
        return {'messages': messages}
