# -*- coding: utf-8 -*-
{
    'name': 'Slovenian Event Venue Management',
    'summary': 'Poroke, konference, dogodki - sale, rezervacije, catering, namestitev, FURS',
    'version': '19.0.1.0.0',
    'category': 'Event Management',
    'description': """
Slovenian Event Venue Management
================================

Za kongresne centre, hot ele z dogodki, poročne dvorane, restavracije z
dogodki, zasebne praznovalske dvorane.

Features
--------
* Venue = lokacija dogodka (npr. hotel X, kongresni center Y)
* Hall = posamezna dvorana/soba znotraj venue-a (večja, manjša, VIP)
* Event = konkreten dogodek (poroka Babic-Kovač 12.6.2025, konferenca TechSI)
* Booking workflow: povpraševanje → ponudba → potrditev → pogodba → izvedba → račun
* Paketi (packages): poročni paket, poslovni sestanek, konferenca, obletnica
* Catering: meniji, pijača, količine glede na število gostov
* Namestitev: povezava z l10n_si_hotel (sobe za goste)
* Časovni potek dogodka (timeline): prihod → sprejem → glavni program → zaključek
* Oprema najem: projektorji, zvok, mikrofoni, odri, mize, stoli
* Dodatne storitve: fotograf, glasba/DJ, cvetje, dekoracija, prevoz
* Pogodbe: generiranje PDF pogodb s podpisom
* Avansno plačilo + končni račun
* Multi-day dogodki (3-dnevne konference)
* FURS davčno potrjevanje preko l10n_si_fiscal
* Statistika: zasedenost dvoran, promet po mesecih, top stranke

Integrations
------------
* `l10n_si_hotel` - povezava sob s poročnimi gosti
* `l10n_si_restaurant` - catering iz restavracije
* `l10n_si_fiscal` - FURS davčno potrjevanje
* `l10n_si_sequence` - številčenje pogodb in računov

Replaces Enterprise `event` + custom venue modules.
""",
    'author': 'markec12345678',
    'website': 'https://github.com/markec12345678/odoo',
    'license': 'LGPL-3',
    'depends': [
        'account',
        'sale_management',
        'calendar',
        'l10n_si',
        'l10n_si_fiscal',
        'l10n_si_sequence',
    ],
    'data': [
        'security/ir.model.access.csv',
        'data/event_venue_data.xml',
        'views/l10n_si_event_venue_views.xml',
        'views/l10n_si_event_hall_views.xml',
        'views/l10n_si_event_package_views.xml',
        'views/l10n_si_event_event_views.xml',
        'views/l10n_si_event_booking_views.xml',
        'views/l10n_si_event_catering_views.xml',
        'views/l10n_si_event_menu.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
    'countries': ['si'],
}
