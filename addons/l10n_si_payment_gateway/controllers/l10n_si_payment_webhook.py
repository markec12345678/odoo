# -*- coding: utf-8 -*-
"""Webhook endpoints for payment providers."""
import json
import logging

from odoo import http
from odoo.http import request

_logger = logging.getLogger(__name__)


class L10nSiPaymentWebhook(http.Controller):
    """Receive payment notifications from external providers."""

    @http.route('/payment/webhook/<string:provider>', type='http', auth='public', methods=['POST'], csrf=False)
    def receive_webhook(self, provider, **kwargs):
        """Receive payment notification from a provider."""
        try:
            body = request.httprequest.data.decode('utf-8')
            _logger.info('Payment webhook from %s: %s', provider, body[:500])

            cfg = request.env['l10n_si.payment.config'].sudo().search([
                ('provider', '=', provider),
                ('active', '=', True),
            ], limit=1)
            if not cfg:
                return 'No config', 404

            # Parse based on provider
            if provider in ('stripe', 'paypal', 'activa'):
                payload = json.loads(body)
                external_id = payload.get('id') or payload.get('transaction_id')
                status = payload.get('status', '').lower()

                tx = request.env['l10n_si.payment.transaction'].sudo().search([
                    ('external_transaction_id', '=', external_id),
                ], limit=1)
                if tx:
                    if status in ('succeeded', 'completed', 'paid'):
                        tx.action_complete()
                    elif status in ('failed', 'declined'):
                        tx.action_fail()
                    elif status in ('refunded', 'cancelled'):
                        tx.action_refund()
                return 'OK', 200

            return 'Unknown provider', 400
        except Exception as e:
            _logger.exception('Payment webhook error: %s', e)
            return str(e), 500

    @http.route('/payment/pay/<string:tx_name>', type='http', auth='public', website=True)
    def payment_page(self, tx_name, **kwargs):
        """Show payment page for a transaction."""
        tx = request.env['l10n_si.payment.transaction'].sudo().search([
            ('name', '=', tx_name),
        ], limit=1)
        if not tx:
            return request.not_found()
        return request.render('l10n_si_payment_gateway.payment_page', {
            'tx': tx,
        })
