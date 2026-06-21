# -*- coding: utf-8 -*-
"""Webhook endpoints for WhatsApp Cloud API."""
import json
import logging

from odoo import http
from odoo.http import request

_logger = logging.getLogger(__name__)


class L10nSiWhatsappWebhook(http.Controller):
    """WhatsApp webhook endpoints.

    Configure in Meta for Developers:
        Webhook URL: https://your-odoo.com/whatsapp/webhook
        Verify Token: <configured on company>
        Subscribed fields: messages, message_status
    """

    @http.route('/whatsapp/webhook', type='http', auth='public', methods=['GET'], csrf=False)
    def verify(self, **kwargs):
        """Webhook verification challenge from Meta."""
        mode = kwargs.get('hub.mode')
        token = kwargs.get('hub.verify_token')
        challenge = kwargs.get('hub.challenge')

        company = request.env['res.company'].sudo().search([
            ('si_whatsapp_verify_token', '=', token),
        ], limit=1)
        if mode == 'subscribe' and company:
            return challenge or ''
        return http.Response('Forbidden', status=403)

    @http.route('/whatsapp/webhook', type='json', auth='public', methods=['POST'], csrf=False)
    def receive(self, **kwargs):
        """Receive incoming WhatsApp messages."""
        try:
            payload = request.get_json_data()
            request.env['l10n_si.whatsapp.message'].sudo().receive_incoming(payload)
        except Exception as e:  # noqa: BLE001
            _logger.warning('Webhook receive error: %s', e)
        return json.dumps({'status': 'ok'})
