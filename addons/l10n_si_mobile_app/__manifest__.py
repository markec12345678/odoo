# -*- coding: utf-8 -*-
{
    'name': 'Slovenian Mobile App (PWA)',
    'summary': 'PWA za terenske delavce + goste - offline-first, installable',
    'version': '19.0.1.0.0',
    'category': 'Mobile',
    'description': """
Slovenian Mobile App (PWA)
==========================

Progressive Web App (PWA) za:
* Hišnike - seznam sob za čiščenje, status update
* Tehnike - maintenance zahteve, foto evidence
* Recepcijo - quick folio view, check-in/out gumbi
* Goste - rezervacije, termini, naročanje room service

Features
--------
* Offline-first (deluje brez interneta, sinhronizira ko je povezava)
* Installable na domač zaslon (Android, iOS, Windows)
* Push notifications
* Touch-optimized UI
* QR code scanner za hitro skeniranje sob
* Geolocation za tehnične obiske
* Photo upload (kamera)
* Biometric login (fingerprint, face)

Routes:
* /mobile - glavni meni PWA
* /mobile/housekeeping - hišništvo
* /mobile/maintenance - tehnik
* /mobile/reception - recepcija
* /mobile/guest - gost
""",
    'author': 'markec12345678',
    'website': 'https://github.com/markec12345678/odoo',
    'license': 'LGPL-3',
    'depends': ['web', 'l10n_si_hotel', 'l10n_si_housekeeping', 'l10n_si_maintenance_request'],
    'data': [
        'security/ir.model.access.csv',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
    'qweb': [
        'views/l10n_si_mobile_app_templates.xml',
    ],
}