# -*- coding: utf-8 -*-
{
    'name': 'Slovenian Camping Management',
    'summary': 'Campsites: parcels (tent/RV/cabin), seasons, check-in/out, FURS davčno potrjevanje',
    'version': '19.0.1.0.0',
    'category': 'Camping',
    'description': """
Slovenian Camping Management
============================

Complete management for Slovenian campsites (kampi).

Features
--------
* Parcele (parcels): šotor, avtodom, prikolica, glamping
* Sezone: nizka/prelivna/visoka sezona + prazniki
* Cenik po tipu parcele × sezona × število oseb
* Check-in / check-out gostov
* Turistična taksa (preko l10n_si_tourist_tax)
* FURS davčno potrjevanje računa (preko l10n_si_fiscal)
* Rezervacije parcel (tudi online)
* Dodatne storitve: elektrika, wifi, prha, pralni stroj, hišni ljubljenčki
* Sanitarna zgradba — število WC/prh na blok
* Akcijske cene za daljše bivanje (7+ dni = -10%)

Standard: po Smaragd (Emerald) kategorizaciji kampov (Zakon o kategorizaciji)
""",
    'author': 'markec12345678',
    'website': 'https://github.com/markec12345678/odoo',
    'license': 'LGPL-3',
    'depends': [
        'account',
        'l10n_si',
        'l10n_si_fiscal',
        'l10n_si_sequence',
    ],
    'data': [
        'security/ir.model.access.csv',
        'data/camping_data.xml',
        'views/l10n_si_camping_parcel_views.xml',
        'views/l10n_si_camping_season_views.xml',
        'views/l10n_si_camping_reservation_views.xml',
        'views/l10n_si_camping_menu.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
    'countries': ['si'],
    'demo': [
        'data/demo_camping_data.xml',
    ],
}
