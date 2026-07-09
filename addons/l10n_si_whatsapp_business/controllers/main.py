import json
import logging
from odoo import http
from odoo.http import request

_logger = logging.getLogger(__name__)


class WhatsAppWebhook(http.Controller):
    @http.route('/wa/webhook', type='json', auth='public', methods=['POST'])
    def webhook_receive(self, **kw):
        """Receive incoming WhatsApp messages via webhook."""
        data = request.get_json_data()
        _logger.info('WhatsApp webhook received: %s', json.dumps(data)[:500])
        try:
            if data.get('object') == 'whatsapp_business_account':
                for entry in data.get('entry', []):
                    for change in entry.get('changes', []):
                        value = change.get('value', {})
                        messages = value.get('messages', [])
                        for msg in messages:
                            phone = msg.get('from', '')
                            text = msg.get('text', {}).get('body', '')
                            if phone and text:
                                request.env['wa.message'].sudo().create({
                                    'phone': phone,
                                    'message_body': text,
                                    'state': 'received',
                                    'direction': 'incoming',
                                    'company_id': request.env.company.id,
                                })
            return {'status': 'ok'}
        except Exception as e:
            _logger.error('WhatsApp webhook error: %s', e)
            return {'status': 'error', 'message': str(e)}

    @http.route('/wa/verify', type='http', auth='public')
    def webhook_verify(self, **kw):
        """Meta webhook verification."""
        mode = kw.get('hub.mode')
        token = kw.get('hub.verify_token')
        challenge = kw.get('hub.challenge')
        company = request.env['res.company'].sudo().search([('wa_verify_token', '=', token)], limit=1)
        if mode == 'subscribe' and company:
            return challenge
        return 'Forbidden', 403
