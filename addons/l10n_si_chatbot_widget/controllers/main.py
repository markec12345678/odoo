# -*- coding: utf-8 -*-
"""Chatbot widget controller — AJAX endpoint za AI odgovore."""
import json
import logging
from odoo import http
from odoo.http import request

_logger = logging.getLogger(__name__)


class ChatbotController(http.Controller):
    @http.route('/chatbot/send', type='json', auth='public', website=True)
    def send_message(self, message, **kwargs):
        """Prejme sporočilo od spletnega widgeta, vrne AI odgovor."""
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
    def get_history(self, conversation_id, **kwargs):
        """Vrni zgodovino pogovora."""
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
