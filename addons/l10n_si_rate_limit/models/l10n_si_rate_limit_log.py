# -*- coding: utf-8 -*-
"""Rate limit log — tracks requests per IP per endpoint."""
import logging
from datetime import datetime, timedelta

from odoo import api, fields, models

_logger = logging.getLogger(__name__)


class L10nSiRateLimitLog(models.Model):
    _name = 'l10n_si.rate.limit.log'
    _description = 'Rate Limit Log Entry'
    _order = 'create_date DESC'
    _rec_name = 'endpoint'

    endpoint = fields.Char(string='Endpoint', required=True, index=True)
    ip_address = fields.Char(string='IP Address', required=True, index=True)
    request_count = fields.Integer(string='Request Count', default=1)
    create_date = fields.Datetime(default=fields.Datetime.now, index=True)

    @api.model
    def cleanup_old_entries(self):
        """Remove entries older than 1 hour."""
        cutoff = fields.Datetime.to_string(datetime.now() - timedelta(hours=1))
        old = self.search([('create_date', '<', cutoff)])
        if old:
            old.unlink()
            _logger.info('Rate limit: cleaned up %d old entries', len(old))

    @api.model
    def check_rate_limit(self, endpoint, ip_address, max_requests, window_seconds=60):
        """Check if request should be allowed.

        Args:
            endpoint: URL path (e.g., '/ai-concierge/chat')
            ip_address: Client IP address
            max_requests: Maximum allowed requests in window
            window_seconds: Time window in seconds (default 60)

        Returns:
            (allowed: bool, remaining: int, retry_after: int)
        """
        now = datetime.now()
        window_start = now - timedelta(seconds=window_seconds)

        # Cleanup old entries periodically (1% chance per request)
        if hash((endpoint, ip_address, now.strftime('%H%M'))) % 100 == 0:
            self.cleanup_old_entries()

        # Count requests in window
        existing = self.search([
            ('endpoint', '=', endpoint),
            ('ip_address', '=', ip_address),
            ('create_date', '>=', fields.Datetime.to_string(window_start)),
        ])

        total_count = sum(rec.request_count for rec in existing)

        if total_count >= max_requests:
            # Rate limited — calculate retry_after
            oldest = existing[-1] if existing else None
            if oldest:
                oldest_time = fields.Datetime.from_string(oldest.create_date)
                retry_after = max(1, int((window_start + timedelta(seconds=window_seconds) - now).total_seconds()))
            else:
                retry_after = window_seconds
            return (False, 0, retry_after)

        # Allowed — log this request
        self.create({
            'endpoint': endpoint,
            'ip_address': ip_address,
            'request_count': 1,
        })

        remaining = max_requests - total_count - 1
        return (True, remaining, 0)

    @api.model
    def get_client_ip(self, request):
        """Extract client IP from request, handling proxies."""
        if not request:
            return '0.0.0.0'
        # Check X-Forwarded-For header (Railway/load balancer)
        forwarded = request.httprequest.environ.get('HTTP_X_FORWARDED_FOR', '')
        if forwarded:
            # X-Forwarded-For can be a comma-separated list; take first (client)
            return forwarded.split(',')[0].strip()
        # Fall back to remote_addr
        return request.httprequest.environ.get('REMOTE_ADDR', '0.0.0.0')
