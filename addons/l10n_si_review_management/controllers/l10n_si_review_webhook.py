# -*- coding: utf-8 -*-
"""Webhook endpoints for receiving review notifications from external platforms."""
import json
import logging

from odoo import http
from odoo.http import request

_logger = logging.getLogger(__name__)


class L10nSiReviewWebhook(http.Controller):
    """Receive webhook notifications when new reviews are posted externally."""

    @http.route('/reviews/webhook/<string:platform>', type='json', auth='public', methods=['POST'], csrf=False)
    def receive_review(self, platform, **kwargs):
        """Receive a review webhook from a specific platform."""
        try:
            payload = request.get_json_data()
            _logger.info('Review webhook from %s: %s', platform, str(payload)[:500])

            # Find the configured source for this platform
            source = request.env['l10n_si.review.source'].sudo().search([
                ('platform', '=', platform),
                ('active', '=', True),
            ], limit=1)
            if not source:
                return json.dumps({'status': 'error', 'message': 'No source configured'})

            # Check for duplicates by external_review_id
            external_id = payload.get('review_id') or payload.get('id')
            if external_id:
                existing = request.env['l10n_si.review'].sudo().search([
                    ('external_review_id', '=', str(external_id)),
                    ('source_id', '=', source.id),
                ], limit=1)
                if existing:
                    return json.dumps({'status': 'ok', 'message': 'Duplicate skipped'})

            # Create the review
            review_vals = {
                'source_id': source.id,
                'external_review_id': str(external_id) if external_id else False,
                'guest_name': payload.get('guest_name', 'Anonimni gost'),
                'title': payload.get('title', ''),
                'body': payload.get('body', payload.get('text', '')),
                'rating': str(payload.get('rating', 5)),
                'review_date': payload.get('date', fields.Datetime.now().isoformat()),
            }
            review = request.env['l10n_si.review'].sudo().create(review_vals)
            return json.dumps({'status': 'ok', 'review_id': review.id})

        except Exception as e:
            _logger.exception('Review webhook error: %s', e)
            return json.dumps({'status': 'error', 'message': str(e)})
