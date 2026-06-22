# -*- coding: utf-8 -*-
{
    'name': 'Slovenian Event Accommodation',
    'summary': 'Blok-rezervacija sob za poročne goste in udeležence konference',
    'version': '19.0.1.0.0',
    'category': 'Event Management',
    'description': """
Slovenian Event Accommodation
==============================

Blokira sobe za:
* Poročne goste (skupinska rezervacija, specialna cena)
* Udeležence konference
* Družinske prireditve

Features
--------
* Block reservation of N rooms for one event
* Special event price (lower than rack rate)
* Release date - do takrat lahko goste rezervira po posebni ceni
* Auto-assign rooms to specific partners
* Integration with l10n_si_hotel for room inventory
* Individual guest bookings via portal
* Report: which rooms still available in block
""",
    'author': 'markec12345678',
    'website': 'https://github.com/markec12345678/odoo',
    'license': 'LGPL-3',
    'depends': ['l10n_si_event_venue', 'l10n_si_hotel'],
    'data': [
        'security/ir.model.access.csv',
        'data/ir_sequence_data.xml',
        'views/l10n_si_event_accommodation_block_views.xml',
        'views/l10n_si_event_accommodation_reservation_views.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
