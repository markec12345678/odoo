# -*- coding: utf-8 -*-
{
    'name': 'Slovenian POS Advanced',
    'summary': 'POS razširitve za hotele/restavracije - FURS, sobe, folio, takse',
    'version': '19.0.1.0.0',
    'category': 'Point of Sale',
    'description': """
Slovenian POS Advanced
======================

POS razširitve specifične za slovenske hotele/restavracije:
* FURS davčno potrjevanje na POS (ZOI/EOR)
* Plačilo na hotelski folio (room charge)
* Avtomatsko dodajanje turistične takse
* Več davčnih stopenj (22% / 9.5% / 5%)
* Tiskanje računa s slovenskimi zahtevami
* Natakar registrira mizo + naročilo
* Davčna številka kupca ob zahtevi
* Povzetek dnevnega prometa (X-poročilo)
* Z-poročilo (dnevni zaključek)
* Lastna plačila (cash drop, inkasso)
* Storno in kopija računa

Integrations:
* `l10n_si_fiscal` - FURS ZOI/EOR
* `l10n_si_hotel` - room charge
* `l10n_si_tourist_tax` - taksa na POS
""",
    'author': 'markec12345678',
    'website': 'https://github.com/markec12345678/odoo',
    'license': 'LGPL-3',
    'depends': ['point_of_sale', 'pos_restaurant', 'l10n_si_fiscal', 'l10n_si_hotel'],
    'data': [
        'security/ir.model.access.csv',
        'data/pos_data.xml',
        'views/pos_config_views.xml',
        'views/pos_session_views.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
