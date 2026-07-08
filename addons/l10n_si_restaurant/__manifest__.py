# -*- coding: utf-8 -*-
{
    'name': 'Slovenian Restaurant Management',
    'summary': 'Menus, tables, reservations, KOT (kitchen order tickets), FURS davčno potrjevanje',
    'version': '19.0.1.0.0',
    'category': 'Restaurant',
    'description': """
Slovenian Restaurant Management
==============================

Restavracija, gostilna, bistro — kompletna rešitev za Slovenijo.

Features
--------
* Jedilnik (menu) z dnevnimi ponudbami
* Kategorije: predjedi, glavne jedi, pijače, sladice
* Alergeni (14 alergenov po EU 1169/2011)
* Mize: floor plan, kapaciteta, rezervacije
* Naročila (KOT = Kitchen Order Ticket) — kuhinja vidi naročila
* Račun (seštevek mize) z avtomatskim FURS davkom
* Tiskanje računa prek tiskalnika
* rezervacije mize za stranke
* Dnevni promet (X-poročilo, Z-poročilo)
* Integracija z l10n_si_fiscal za ZOI/EOR

Integracije
-----------
* `l10n_si_fiscal` — davčno potrjevanje računa
* `l10n_si_sequence` — številčenje računov (REST1-KASA1-2025-00001)
* `pos_restaurant` (community) — POS za natakarje

Replaces Enterprise restaurant extensions.
""",
    'author': 'markec12345678',
    'website': 'https://github.com/markec12345678/odoo',
    'license': 'LGPL-3',
    'depends': [
        'account',
        'pos_restaurant',
        'l10n_si',
        'l10n_si_fiscal',
        'l10n_si_sequence',
    ],
    'data': [
        'security/ir.model.access.csv',
        'data/restaurant_data.xml',
        'views/l10n_si_restaurant_menu_views.xml',
        'views/l10n_si_restaurant_reservation_views.xml',
        'views/l10n_si_restaurant_kot_views.xml',
        'views/restaurant_menu.xml',
        'views/l10n_si_restaurant_table_views.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
    'countries': ['si'],
    'demo': [
        'data/demo_restaurant_data.xml',
    ],
    'qweb': [
    ],
}