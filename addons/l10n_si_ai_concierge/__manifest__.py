# -*- coding: utf-8 -*-
{
    'name': 'Slovenian AI Concierge',
    'summary': 'AI asistent za goste v slovenščini - informacije, priporočila, rezervacije',
    'version': '19.0.1.2.0',
    'category': 'Hospitality',
    'description': """
Slovenian AI Concierge
======================

AI asistent (chatbot) za goste hotele/restavracije/kampa:
* Odgovarja na pogosta vprašanja v slovenščini (WiFi geslo, ura zajtrka, ...)
* Priporoča lokalne atrakcije, restavracije, prevoze
* Lahko rezervira masaže, mize, aktivnosti
* Večkontekstno: pozna zgodovino pogovora
* Multichannel: spletni chat, WhatsApp, email
* 24/7 dostopen
* Stalno učenje iz povratnih informacij gostov

Backend:
* OpenAI GPT-4 / Anthropic Claude / ZAI
* Slovenski jezik z dodatnim kontekstom o SI zakonodaji
* Knowledge base iz l10n_si_knowledge modula

Integrations:
* `l10n_si_knowledge` - baza znanja (FAQ, postopki)
* `l10n_si_hotel` - sobe, razpoložljivost
* `l10n_si_restaurant` - mize, meniji
* `l10n_si_wellness` - termini
* `l10n_si_whatsapp` - WhatsApp dostop
""",
    'author': 'markec12345678',
    'website': 'https://github.com/markec12345678/odoo',
    'license': 'LGPL-3',
    'depends': ['mail', 'l10n_si_knowledge', 'l10n_si_whatsapp'],
    'data': [
        'security/ir.model.access.csv',
        'data/ai_concierge_data.xml',
        'views/l10n_si_ai_concierge_config_views.xml',
        'views/l10n_si_ai_concierge_conversation_views.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
