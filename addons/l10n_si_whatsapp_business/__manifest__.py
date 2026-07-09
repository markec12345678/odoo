# -*- coding: utf-8 -*-
{
    'name': 'WhatsApp Business API (SI)',
    'summary': 'WhatsApp Cloud API integration — send messages, templates, notifications',
    'version': '19.0.1.0.0',
    'category': 'Discuss',
    'description': """
WhatsApp Business API (SI)
==========================

Integrates WhatsApp Cloud API (Meta) for sending messages to customers:
* Send text messages, templates, and media via WhatsApp
* Automatic notifications: invoice confirmed, reservation confirmed, check-in reminder
* Template management (pre-approved Meta templates)
* Two-way messaging (receive webhooks from WhatsApp)
* Multi-company support (each company has its own WhatsApp number)

Configuration:
    * Settings → Companies → WhatsApp tab
    * Enter Phone Number ID and Access Token from Meta Business Suite
    * Register webhook URL for incoming messages

Requires:
    * Meta Business Account with WhatsApp Business API enabled
    * Permanent access token from Meta App Dashboard

References:
    * WhatsApp Cloud API: https://developers.facebook.com/docs/whatsapp/cloud-api
    * Meta Business Suite: https://business.facebook.com
""",
    'author': 'markec12345678',
    'website': 'https://github.com/markec12345678/odoo',
    'license': 'LGPL-3',
    'depends': ['base', 'mail', 'account'],
    'data': [
        'security/ir.model.access.csv',
        'views/res_company_views.xml',
        'views/whatsapp_message_views.xml',
        'views/whatsapp_template_views.xml',
        'views/whatsapp_menu.xml',
    ],
    'installable': True,
    'application': True,
}
