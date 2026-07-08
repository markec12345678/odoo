# -*- coding: utf-8 -*-
{
    'name': 'Slovenian Helpdesk (Simple)',
    'summary': 'Customer support ticket system with SLA tracking — replaces Enterprise Helpdesk',
    'version': '19.0.1.0.0',
    'category': 'Services/Helpdesk',
    'description': """
Slovenian Helpdesk (Simple)
============================

Lightweight customer support ticketing system for Odoo Community 19.0.
Replaces Enterprise `helpdesk` module for Slovenian small/medium businesses.

Features
--------
* Teams (prodaja, tehnična podpora, reklamnacije, ...)
* Ticket lifecycle with stages (Novo → V obravnavi → Čaka odgovor → Rešeno → Zaprto)
* SLA tracking per team (response time, resolution time)
* Customer portal — customers can submit and track their own tickets
* Email integration — incoming emails auto-create tickets
* Priority levels (Nizka, Srednja, Visoka, Nujno)
* Time tracking per ticket
* Canned responses (predloge odgovorov)
* Tags for categorization
* Auto-assignment by team round-robin
* Audit log of all state changes

Configuration
-------------
1. Helpdesk → Configuration → Teams → Create
2. Set SLA: response time (e.g. 4h), resolution time (e.g. 48h)
3. Set email alias for incoming tickets
4. Configure stages per team

References
----------
* Slovenian consumer protection law (ZVPot) — 8 days response for reclamations
* ISO 10002 (complaint handling) guidelines
""",
    'author': 'markec12345678',
    'website': 'https://github.com/markec12345678/odoo',
    'license': 'LGPL-3',
    'depends': [
        'base',
        'mail',
        'portal',
        'rating',
    ],
    'data': [
        'security/ir.model.access.csv',
        'security/helpdesk_security.xml',
        'data/l10n_si_helpdesk_data.xml',
        'views/l10n_si_helpdesk_team_views.xml',
        'views/l10n_si_helpdesk_stage_views.xml',
        'views/l10n_si_helpdesk_canned_response_views.xml',
        'views/l10n_si_helpdesk_ticket_views.xml',
        'views/l10n_si_helpdesk_menu.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
    'qweb': [
        'views/l10n_si_helpdesk_portal_templates.xml',
    ],
}