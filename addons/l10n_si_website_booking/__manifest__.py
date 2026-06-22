# -*- coding: utf-8 -*-
{
    'name': 'Slovenian Website Booking Engine',
    'summary': 'Spletni booking engine za hotel/kamp - direktno rezerviranje brez provizij',
    'version': '19.0.1.0.0',
    'category': 'Website',
    'description': """
Slovenian Website Booking Engine
================================

Lastni booking engine na spletni strani (brez provizij OTAs):
* Iskanje prostih sob/parcel po datumih
* Prikaz cen iz l10n_si_revenue_management (dinamično)
* Spletni obrazec za rezervacijo
* Spletno plačilo (preko l10n_si_payment_gateway)
* Potrditev rezervacije po e-pošti
* Večjezični vmesnik (slovenščina, angleščina, nemščina, italijanščina)
* Mobilno prilagojen design
* Integracija z l10n_si_channel_manager (sinhronizirana razpoložljivost)
* Promo kodni sistem (npr. EARLYBIRD20, SUMMER10)
* Spletna stran: /book - iskanje, /book/checkout - plačilo, /book/confirm - potrditev
""",
    'author': 'markec12345678',
    'website': 'https://github.com/markec12345678/odoo',
    'license': 'LGPL-3',
    'depends': ['website', 'l10n_si_hotel', 'l10n_si_camping', 'l10n_si_revenue_management'],
    'data': [
        'security/ir.model.access.csv',
        'data/booking_data.xml',
        'views/l10n_si_booking_promo_views.xml',
        'views/l10n_si_website_booking_templates.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
