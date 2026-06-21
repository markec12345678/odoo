# -*- coding: utf-8 -*-
{
    'name': 'Slovenian WhatsApp Integration',
    'summary': 'Send WhatsApp messages to customers + receive replies — replaces Enterprise WhatsApp',
    'version': '19.0.1.0.0',
    'category': 'Discuss/WhatsApp',
    'description': """
Slovenian WhatsApp Integration
===============================

Send and receive WhatsApp messages from Odoo.

Features:
* Send WhatsApp message from any record (partner, invoice, ticket)
* Receive replies via webhook (Twilio or WhatsApp Cloud API)
* Templates with placeholders
* Auto-send on triggers (invoice issued, ticket updated)
* Bulk send to filtered partner list
* Conversation view per partner
* Opt-in / opt-out management (GDPR)
* File attachments (PDF, images)

Backends:
* WhatsApp Cloud API (Meta official, free for first 1000 conversations/month)
* Twilio WhatsApp API (paid, more reliable)

Replaces Enterprise `whatsapp`.
""",
    'author': 'markec12345678',
    'website': 'https://github.com/markec12345678/odoo',
    'license': 'LGPL-3',
    'depends': ['mail', 'base'],
    'data': [
        'security/ir.model.access.csv',
        'views/res_company_views.xml',
        'views/l10n_si_whatsapp_message_views.xml',
        'views/l10n_si_whatsapp_template_views.xml',
        'views/res_partner_views.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
