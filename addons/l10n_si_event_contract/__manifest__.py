# -*- coding: utf-8 -*-
{
    'name': 'Slovenian Event Contract',
    'summary': 'Generiranje PDF pogodb z eIDAS podpisom za dogodke',
    'version': '19.0.1.0.0',
    'category': 'Event Management',
    'description': """
Slovenian Event Contract
========================

Avtomatsko generiranje pogodb za:
* Poročne pogodbe
* Konferenčne pogodbe
* Najemne pogodbe za dvorane
* Sponsorske pogodbe

Features
--------
* Predloge (templates) z mail-merge placeholderji
* Avtomatsko polnjenje iz podatkov o dogodku
* PDF izvoz z glavo/nogo podjetja
* eIDAS podpis preko l10n_si_sign modula
* Status workflow: osnutek → poslano → podpisano → arhivirano
* Dvojno podpisovanje (stranka + organizator)
* Hramba 10 let
* Vrstni red podpisov (stranka najprej, organizator drugi)
""",
    'author': 'markec12345678',
    'website': 'https://github.com/markec12345678/odoo',
    'license': 'LGPL-3',
    'depends': ['l10n_si_event_venue', 'l10n_si_sign'],
    'data': [
        'security/ir.model.access.csv',
        'data/contract_data.xml',
        'views/l10n_si_event_contract_template_views.xml',
        'views/l10n_si_event_contract_views.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
