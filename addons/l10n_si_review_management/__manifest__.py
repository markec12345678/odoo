# -*- coding: utf-8 -*-
{
    'name': 'Slovenian Review Management',
    'summary': 'Integracija z Booking.com/TripAdvisor/Google reviews + AI analiza',
    'version': '19.0.1.0.0',
    'category': 'Customer Relationship',
    'description': """
Slovenian Review Management
===========================

Centralizirano upravljanje ocen in mnenj gostov:
* Pridobivanje ocen z:
  - Booking.com (preko XML API)
  - TripAdvisor (preko Content API)
  - Google Reviews (preko Business API)
  - Airbnb (preko API)
  - interni obrazci (po obisku)
* AI analiza sentiment-a (pozitivno/negativno/mešano)
* Kategorizacija težav (čistoča, osebje, hrana, lokacija, cena)
* Avtomatski odgovori (AI predlog)
* Tracking response time
* Alerts za nizke ocene (1-2 zvezdici)
* Poročilo trenda (mesečno, letno)
* Nalaganje slik ocen
""",
    'author': 'markec12345678',
    'website': 'https://github.com/markec12345678/odoo',
    'license': 'LGPL-3',
    'depends': ['mail', 'l10n_si_hotel'],
    'data': [
        'security/ir.model.access.csv',
        'data/review_data.xml',
        'views/l10n_si_review_views.xml',
        'views/l10n_si_review_source_views.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
