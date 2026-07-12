# -*- coding: utf-8 -*-
"""Rate limit configuration — configurable limits per endpoint."""
from odoo import api, fields, models


class L10nSiRateLimitConfig(models.Model):
    _name = 'l10n_si.rate.limit.config'
    _description = 'Rate Limit Configuration'
    _order = 'endpoint'

    name = fields.Char(string='Description', compute='_compute_name', store=True)
    endpoint = fields.Char(string='Endpoint URL', required=True,
                            help='URL path, e.g. /ai-concierge/chat')
    max_requests = fields.Integer(
        string='Max Requests',
        required=True,
        default=10,
        help='Maximum requests allowed in the time window',
    )
    window_seconds = fields.Integer(
        string='Window (seconds)',
        required=True,
        default=60,
        help='Time window in seconds (default: 60 = per minute)',
    )
    active = fields.Boolean(string='Active', default=True)
    whitelisted_ips = fields.Text(
        string='Whitelisted IPs',
        help='One IP per line. These IPs bypass rate limiting.\n'
             'Use for trusted services (e.g., Meta webhook IPs).',
    )
    company_id = fields.Many2one(
        'res.company', string='Company',
        default=lambda self: self.env.company, required=True,
    )

    _sql_constraints = [
        ('endpoint_unique', 'unique(endpoint, company_id)',
         'Rate limit for this endpoint already exists!'),
    ]

    @api.depends('endpoint', 'max_requests', 'window_seconds')
    def _compute_name(self):
        for cfg in self:
            cfg.name = f'{cfg.endpoint} ({cfg.max_requests}/{cfg.window_seconds}s)'

    @api.model
    def get_config_for_endpoint(self, endpoint):
        """Get rate limit config for a given endpoint.

        Returns dict with 'max_requests', 'window_seconds', 'whitelisted_ips'
        or None if no config found.
        """
        cfg = self.search([
            ('endpoint', '=', endpoint),
            ('active', '=', True),
        ], limit=1)
        if not cfg:
            return None
        whitelist = []
        if cfg.whitelisted_ips:
            whitelist = [
                ip.strip() for ip in cfg.whitelisted_ips.split('\n')
                if ip.strip()
            ]
        return {
            'max_requests': cfg.max_requests,
            'window_seconds': cfg.window_seconds,
            'whitelisted_ips': whitelist,
        }

    @api.model
    def is_ip_whitelisted(self, endpoint, ip_address):
        """Check if an IP is whitelisted for a given endpoint."""
        config = self.get_config_for_endpoint(endpoint)
        if not config:
            return False
        return ip_address in config['whitelisted_ips']
