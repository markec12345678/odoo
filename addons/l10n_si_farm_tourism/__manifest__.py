# -*- coding: utf-8 -*-
{
    'name': 'Slovenian Farm Tourism (Kmečki turizem)',
    'summary': 'Sobe na kmetiji, domači izdelki, agroturizem, FURS, kmetijska evidence',
    'version': '19.0.1.0.0',
    'category': 'Farm Tourism',
    'description': """
Slovenian Farm Tourism (Kmečki turizem)
========================================

Za kmečke turistične kmetije, agroturizem, turistične kmetije.

Features
--------
* Sobe na kmetiji (manjši obseg kot hotel - tipično 5-15 ležišč)
* Domači izdelki (prodaja na kmetiji):
  - Sir, mleko, jajca, meso, pršut, med, žganci, žganje
  - Z certifikati "Kmetijski kmetijski izdelek" / "Po kmetijskih pridelovalcih"
* Kmetijska evidenca (na voljo preko OCA vertical-agriculture integracije)
* Meniji za kosilo (del kmetije) - tipično 3-5hodovni
* Degustacije vina / žganja
* Delavnice (sirarstvo, kruh, moko)
* Program "Kmečka opravila" - turisti pomagajo pri kmetijskih delih
* Povezava z EKO certifikati (Biodar, Kontrakt)
* FURS davčno potrjevanje (tudi za maloprodajo domačih izdelkov)
* Turistična taksa (preko l10n_si_tourist_tax)
* Subvencije APJ (Agencija za kmetijstvo in gozdarstvo)

Legal basis
-----------
* Pravilnik o kmetijstvu in kmetijskem turizmu (UR. l. RS š. 51/15)
* Zakon o kmetijstvu (ZKme)
* SMGT (Slovenska mreža gostiln in turizma na kmetiji) standardi
""",
    'author': 'markec12345678',
    'website': 'https://github.com/markec12345678/odoo',
    'license': 'LGPL-3',
    'depends': [
        'account',
        'stock',
        'l10n_si',
        'l10n_si_fiscal',
        'l10n_si_sequence',
    ],
    'data': [
        'security/ir.model.access.csv',
        'data/farm_tourism_data.xml',
        'views/l10n_si_farm_room_views.xml',
        'views/l10n_si_farm_product_views.xml',
        'views/l10n_si_farm_reservation_views.xml',
        'views/l10n_si_farm_menu.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
    'countries': ['si'],
}
