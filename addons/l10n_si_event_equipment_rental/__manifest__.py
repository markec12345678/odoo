# -*- coding: utf-8 -*-
{
    'name': 'Slovenian Event Equipment Rental',
    'summary': 'Najem opreme za dogodke - projektorji, zvok, odri, mize, stoli',
    'version': '19.0.1.0.0',
    'category': 'Event Management',
    'description': """
Slovenian Event Equipment Rental
================================

Najem opreme za dogodke z ločenim računom:
* AV oprema: projektorji, platna, mikrofoni, zvočniki, mešalke
* Scenska oprema: odri, reflektorji, dimnik
* Pohištvo: mize (okrogle, pravokotne), stoli, tribune
* Dekoracija: cvetje, preproge, prevleke
* Tehnična podpora: tehnik na kraju samem

Features
--------
* Inventory opreme (koliko kosov imamo na zalogi)
* Najem po urah/dneh
* Kalendarski pregled zasedenosti opreme
* Tehnična podpora kot dodaten artikel
* Avtomatski izračun konflikta (isto opremo potrebujejo dva dogodka)
* Račun ločeno od dvorane
""",
    'author': 'markec12345678',
    'website': 'https://github.com/markec12345678/odoo',
    'license': 'LGPL-3',
    'depends': ['l10n_si_event_venue'],
    'data': [
        'security/ir.model.access.csv',
        'data/equipment_data.xml',
        'views/l10n_si_event_equipment_views.xml',
        'views/l10n_si_event_equipment_rental_views.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
