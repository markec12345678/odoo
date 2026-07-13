# -*- coding: utf-8 -*-
"""WhatsApp webhook controller — sprejema webhook od Meta."""
import json
import logging
from odoo import http
from odoo.http import request

_logger = logging.getLogger(__name__)


class WhatsAppWebhook(http.Controller):
    @http.route('/whatsapp/webhook', type='http', auth='public', methods=['GET'], csrf=False)
    def verify_webhook(self, **kwargs):
        """Meta pošlje GET za verifikacijo webhook-a."""
        verify_token = kwargs.get('hub.verify_token')
        challenge = kwargs.get('hub.challenge')
        company = request.env['res.company'].sudo().search([('wa_verify_token', '=', verify_token)], limit=1)
        if company:
            return challenge
        return 'Forbidden', 403

    @http.route('/whatsapp/webhook', type='json', auth='public', methods=['POST'], csrf=False)
    def receive_webhook(self, **kwargs):
        """Meta pošlja POST za status dostave in vhodna sporočila."""
        try:
            data = request.get_json_data()
            for entry in data.get('entry', []):
                for change in entry.get('changes', []):
                    value = change.get('value', {})
                    # Status updates (delivered, read)
                    for status in value.get('statuses', []):
                        msg_id = status.get('id')
                        status_val = status.get('status')
                        if msg_id and status_val:
                            msg = request.env['l10n_si.whatsapp.message'].sudo().search([
                                ('wa_message_id', '=', msg_id)
                            ], limit=1)
                            if msg:
                                msg.write({'state': status_val})
                    # Incoming messages
                    for msg in value.get('messages', []):
                        phone = msg.get('from')
                        text = msg.get('text', {}).get('body', '')
                        if phone and text:
                            partner = request.env['res.partner'].sudo().search([
                                '|', ('mobile', 'ilike', phone), ('phone', 'ilike', phone)
                            ], limit=1)
                            if partner:
                                incoming = request.env['l10n_si.whatsapp.message'].sudo().create({
                                    'partner_id': partner.id,
                                    'direction': 'incoming',
                                    'message_type': 'text',
                                    'body': text,
                                })
                                # AI auto-reply (if enabled + AI Core installed)
                                try:
                                    request.env['l10n_si.whatsapp.message'].sudo().auto_reply_to_incoming(incoming)
                                except Exception as ar_err:
                                    _logger.debug('Auto-reply skipped: %s', ar_err)
        except Exception as e:
            _logger.error('WhatsApp webhook error: %s', e)
        return {'status': 'ok'}
