# -*- coding: utf-8 -*-
{
    'name': 'Slovenian Hotel Housekeeping',
    'summary': 'Hišništvo - čistilni plan, sledenje stanju sob, task dodelitev',
    'version': '19.0.1.0.0',
    'category': 'Hotel Management',
    'description': """
Slovenian Hotel Housekeeping
============================

Hišništvo za hotele:
* Čistilni načrt (dnevni pregled sob)
* Sledenje stanju: prosta/čisti se/vzdrževanje
* Dodelitev sob hišnikom (housekeeper)
* Časovni listi hišnikov (koliko časa na sobo)
* Poročilo o najdenih poškodbah/izgubljenih predmetih
* Mini-bar inventory (pregled pred pripravo)
* Lost & Found - izgubljeni predmeti gostov
* Sprotno beleženje porabe čistil
* Priority: normalna, nujna (za vip ali check-in)
* Cron: ob 6:00 generira dnevni čistilni seznam
""",
    'author': 'markec12345678',
    'website': 'https://github.com/markec12345678/odoo',
    'license': 'LGPL-3',
    'depends': ['l10n_si_hotel', 'hr'],
    'data': [
        'security/ir.model.access.csv',
        'data/housekeeping_data.xml',
        'views/l10n_si_housekeeping_lost_found_views.xml',
        'views/hr_employee_views.xml',
        'views/l10n_si_housekeeping_task_views.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
    'qweb': [
    ],
}