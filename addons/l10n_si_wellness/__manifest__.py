# -*- coding: utf-8 -*-
{
    'name': 'Slovenian Wellness & Spa',
    'summary': 'Masaže, savne, bazeni, paketi - za hotele z wellnessom',
    'version': '19.0.1.0.0',
    'category': 'Hospitality',
    'description': """
Slovenian Wellness & Spa
========================

Wellness center management:
* Terme (savne, bazeni, parne kopeli)
* Masaže in behandlungen
* Lepotni programi
* Paketi (1-dnevni, 3-dnevni, 7-dnevni)
* Rezervacije termina pri maserju/terapevtu
* Day pass za zunanjje goste
* Combo s hotelsko prenočitev
* FURS davčno potrjevanje
* Pristopbine (Entry fees) po kategorijah

Kategorije gostov:
* Odrasli
* Otroci 0-6 (brezplačno)
* Otroci 7-15 (50% popust)
* Družinski paket (2+2)
* Seniorji 65+ (20% popust)
* Študenti (10% popust)
""",
    'author': 'markec12345678',
    'website': 'https://github.com/markec12345678/odoo',
    'license': 'LGPL-3',
    'depends': ['l10n_si', 'l10n_si_fiscal', 'l10n_si_sequence', 'resource'],
    'data': [
        'security/ir.model.access.csv',
        'data/wellness_data.xml',
        'views/l10n_si_wellness_service_views.xml',
        'views/l10n_si_wellness_booking_views.xml',
        'views/l10n_si_wellness_pass_views.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
