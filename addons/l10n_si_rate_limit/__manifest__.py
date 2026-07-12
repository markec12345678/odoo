# -*- coding: utf-8 -*-
{
    'name': 'SI/HR Rate Limiting',
    'summary': 'Rate limiting for public API endpoints — prevents abuse',
    'version': '19.0.1.0.0',
    'category': 'Services',
    'description': """
SI/HR Rate Limiting
===================

Rate limiting for public API endpoints (AI Concierge, Chatbot Widget,
WhatsApp webhook). Prevents abuse by tracking requests per IP address.

Default limits:
- AI Concierge (/ai-concierge/chat): 10 requests/minute per IP
- Chatbot Widget (/chatbot/send): 10 requests/minute per IP
- WhatsApp Webhook (/whatsapp/webhook): 60 requests/minute per IP

When limit exceeded, returns HTTP 429 (Too Many Requests) with
Retry-After header.

Configuration:
- Limits configurable per endpoint in Settings → Technical → Rate Limits
- Whitelist for trusted IPs (e.g., Meta webhook IPs, Railway healthcheck)

Implementation:
- Uses ir.logging table for tracking (auto-cleaned by Odoo)
- Per-IP tracking with sliding window
- Automatic cleanup of entries older than window size
""",
    'author': 'markec12345678',
    'website': 'https://github.com/markec12345678/odoo',
    'license': 'LGPL-3',
    'depends': ['base', 'web'],
    'data': [
        'security/ir.model.access.csv',
        'views/l10n_si_rate_limit_config_views.xml',
    ],
    'installable': True,
    'auto_install': False,
}
