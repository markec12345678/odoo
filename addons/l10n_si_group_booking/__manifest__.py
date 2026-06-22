# -*- coding: utf-8 -*-
{
    'name': 'Slovenian Group Booking',
    'summary': 'Skupinske rezervacije za potovalne agencije, šole, podjetja',
    'version': '19.0.1.0.0',
    'category': 'Hotel Management',
    'description': """
Slovenian Group Booking
=======================

Skupinske rezervacije za:
* Potovalne agencije (turisticne ture)
* Šolske izlete
* Podjetniška srečanja
* Športne ekipe
* Družinska srečanja (poroke, obletnice)

Features
--------
* Ena skupinska rezervacija = N sob
* Agency commission (provizija) — 5-15%
* Special group price (pogajanje)
* Cut-off date — do takrat lahko še dodaja/odvzema sobe
* Allocation release — nezasedene sobe se sprostijo na določen dan
* Rooming list — kateri gost je v kateri sobi
* Skupinski obračun na eno fakture (ali individualni obračuni)
* Free leader — vsakih 20 gostov 1 brezplačna soba
* Paketne cene (polpenzion, penzion, all-inclusive)
* Prevoz od/do letališča (opcijsko)
""",
    'author': 'markec12345678',
    'website': 'https://github.com/markec12345678/odoo',
    'license': 'LGPL-3',
    'depends': ['l10n_si_hotel', 'l10n_si_event_venue'],
    'data': [
        'security/ir.model.access.csv',
        'data/ir_sequence_data.xml',
        'views/l10n_si_group_booking_views.xml',
        'views/l10n_si_rooming_list_views.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
