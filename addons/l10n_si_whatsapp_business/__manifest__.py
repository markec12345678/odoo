# -*- coding: utf-8 -*-
{
    'name': 'WhatsApp Business Cloud API',
    'summary': 'Pošiljanje WhatsApp sporočil preko WhatsApp Cloud API (Meta)',
    'version': '19.0.1.2.0',
    'category': 'Discuss',
    'description': """
WhatsApp Business Cloud API
============================

Pošiljanje WhatsApp sporočil preko uradne Meta WhatsApp Cloud API.

Funkcionalnosti:
* Pošiljanje besedilnih sporočil
* Pošiljanje predlog (templates) - potrditve rezervacij, opomniki
* Sprejemanje webhook sporočil (dostave, prebrano)
* Automatska potrditev rezervacije preko WhatsApp
* Opomnik za check-in 24h pred prihodom
* Multi-company support (vsako podjetje ima svojo WhatsApp številko)

Konfiguracija:
1. Pridobite WhatsApp Business API dostop na https://developers.facebook.com/apps/
2. Settings → WhatsApp → vnesite Phone Number ID in Access Token
3. Registrirajte webhook URL na Meta dashboard

Pravne podlage:
* GDPR člen 6(1)(f) - legitimen interes (potrditev rezervacije)
* UPORABNIK MORA DATI STRINJANJE za WhatsApp komunikacijo
""",
    'author': 'markec12345678',
    'website': 'https://github.com/markec12345678/odoo',
    'license': 'LGPL-3',
    'depends': ['base', 'mail'],
    'data': [
        'security/ir.model.access.csv',
        'data/ir_sequence_data.xml',
        'data/ir_cron_data.xml',
        'data/whatsapp_templates.xml',
        'views/res_company_views.xml',
        'views/l10n_si_whatsapp_message_views.xml',
        'views/l10n_si_whatsapp_template_views.xml',
        'views/l10n_si_whatsapp_menu.xml',
    ],
    'installable': True,
    'application': True,
}
