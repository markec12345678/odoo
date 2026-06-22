# -*- coding: utf-8 -*-
{
    'name': 'Slovenian Hotel Management',
    'summary': 'Hotel PMS: rooms, reservations, folio, check-in/out with FURS davčno potrjevanje',
    'version': '19.0.1.0.0',
    'category': 'Hotel Management',
    'description': """
Slovenian Hotel Management
==========================

Complete Property Management System (PMS) for Slovenian hotels, gostilne
with rooms, and tourist accommodations.

Based on OCA/vertical-hotel (SerpentCS), ported to Odoo 19.0 with:

* Sobe, vrste sob, amenities (per OCA structure)
* Rezervacije s folio (Folio = grupirani račun gosta)
* Check-in / check-out workflow
* Avtomatsko generiranje računov ob odjavu
* FURS davčno potrjevanje (ZOI/EOR) preko `l10n_si_fiscal`
* Cenik po sezonah (visoka/nizka sezona, prazniki, weekends)
* Channel manager hook (Booking.com / Airbnb preko l10n_si_channel_manager)
* Spletna rezervacija (preko website_portal)
* Večvalutno (EUR + tuje)
* Skupinski obračun (group folio)
* Storitve: minibar, sobna storitev, pralnica — z FURS davkom
* Reporting: zasedenost, ADR, RevPAR

Requires:
* l10n_si_fiscal (for ZOI/EOR on folio invoices)
* l10n_si_sequence (for BL1-RECEP1-2025-00001 numbering)

Origin: https://github.com/OCA/vertical-hotel/tree/17.0/hotel
License: LGPL-3 (per OCA manifest)
""",
    'author': 'markec12345678 (ported from OCA/vertical-hotel by SerpentCS)',
    'website': 'https://github.com/markec12345678/odoo',
    'license': 'LGPL-3',
    'depends': [
        'sale_stock',
        'account',
        'l10n_si',
        'l10n_si_fiscal',
        'l10n_si_sequence',
    ],
    'data': [
        'security/ir.model.access.csv',
        'security/hotel_security.xml',
        'data/hotel_sequence.xml',
        'data/hotel_data.xml',
        'views/hotel_room_views.xml',
        'views/hotel_room_type_views.xml',
        'views/hotel_folio_views.xml',
        'views/hotel_reservation_views.xml',
        'views/hotel_service_views.xml',
        'views/hotel_menu.xml',
        'reports/hotel_folio_report.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
    'countries': ['si'],
}
