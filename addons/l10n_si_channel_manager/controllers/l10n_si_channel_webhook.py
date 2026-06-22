# -*- coding: utf-8 -*-
"""Webhook endpoints for receiving channel notifications (new reservations, cancellations)."""
import json
import logging

from odoo import http
from odoo.http import request

_logger = logging.getLogger(__name__)


class L10nSiChannelWebhook(http.Controller):
    """Webhook endpoints.

    Vsak kanal ima svoj endpoint:
    * /channel/booking_com/webhook
    * /channel/airbnb/webhook
    * /channel/expedia/webhook
    """

    @http.route('/channel/<string:channel>/webhook', type='json', auth='public', methods=['POST'], csrf=False)
    def receive_webhook(self, channel, **kwargs):
        """Receive webhook from any channel."""
        try:
            payload = request.get_json_data()
            _logger.info('Channel webhook received: %s, payload keys: %s',
                         channel, list(payload.keys()) if isinstance(payload, dict) else 'not-dict')

            # Find channel config
            cfg = request.env['l10n_si.channel.config'].sudo().search([
                ('channel', '=', channel),
                ('state', '=', 'active'),
            ], limit=1)
            if not cfg:
                return json.dumps({'status': 'error', 'message': 'No active config for channel'})

            # Log the webhook
            request.env['l10n_si.channel.log'].sudo().create({
                'channel_config_id': cfg.id,
                'log_type': 'reservation_pull',
                'state': 'success',
                'message': f'Webhook received: {json.dumps(payload)[:500]}',
                'raw_payload': json.dumps(payload)[:10000],
            })

            # Process based on channel type
            if channel == 'booking_com':
                cfg._process_booking_com_webhook(payload)
            elif channel == 'airbnb':
                cfg._process_airbnb_webhook(payload)
            elif channel == 'expedia':
                cfg._process_expedia_webhook(payload)

            return json.dumps({'status': 'ok'})

        except Exception as e:
            _logger.exception('Channel webhook error: %s', e)
            return json.dumps({'status': 'error', 'message': str(e)})
