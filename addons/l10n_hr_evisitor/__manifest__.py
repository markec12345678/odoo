# -*- coding: utf-8 -*-
{
    'name': 'Croatian eVisitor — Tourist Guest Registration',
    'summary': 'HTZ eVisitor REST API — prijava i odjava turista, obračun boravišne pristojbe',
    'version': '19.0.1.0.0',
    'category': 'Accounting/Localizations',
    'description': """
Croatian eVisitor — Tourist Guest Registration (HTZ)
====================================================

Integracija s **eVisitor** sustavom Hrvatske turističke zajednice (HTZ)
za prijavu i odjavu turista te obračun boravišne pristojbe putem REST API-ja.

Zakonska osnova:
* Zakon o pružanju usluga u turizmu (UR. l. RH š. 68/13, 85/15, 30/18, 62/20, 32/23)
* Zakon o boravišnoj pristojbi (UR. l. RH š. 152/08, 59/09, 78/12, 56/16, 25/23)

Značajke
--------
* **Prijava turista** (CheckIn) — slanje podataka o gostu i smještaju
* **Odjava turista** (CheckOut) — odjava gosta prije odlaska
* **Obračun boravišne pristojbe** — automatski izračun na temelju broja noćenja
* **Mogućnosti** (smještajni objekti) — hotel, apartman, soba, kamp, vila, kuća, brod, ostalo
* **Dnevnik audita** — svaki API poziv zabilježen za 5 godina
* **Više okolina** — TEST (eVisitorRhetos_API/Rest/_test/) / PROD (eVisitorRhetos_API/Rest/)
* **HTTP Basic Auth** — korisničko ime/lozinka izdano od strane HTZ-a
* **Automatski cron** — obrada pending prijava (15 min) i ponovni pokušaj grešaka (15 min)
* **Multi-company** — podrška za više tvrtki s odvojenim konfiguracijama

API endpointi (REST + JSON):
- PROD: https://www.evisitor.hr/eVisitorRhetos_API/Rest/
- TEST: https://www.evisitor.hr/eVisitorRhetos_API/Rest/_test/

Operacije:
- POST  /CheckIn        — prijava gosta
- POST  /CheckOut       — odjava gosta
- GET   /GetTouristTax  — izračun boravišne pristojbe
- GET   /ListCountries  — popis država
- GET   /Ping           — provjera povezanosti

Reference
----------
* HTZ eVisitor: https://www.evisitor.hr/
* Tehnička dokumentacija eVisitor REST API v2.x
* Zakon o boravišnoj pristojbi (UR. l. RH š. 152/08, 59/09, 78/12, 56/16, 25/23)
* Zakon o pružanju usluga u turizmu (UR. l. RH š. 68/13, 85/15, 30/18, 62/20, 32/23)
""",
    'author': 'markec12345678',
    'website': 'https://github.com/markec12345678/odoo',
    'license': 'LGPL-3',
    'depends': [
        'l10n_hr',
        'l10n_hr_fiscal',
    ],
    'data': [
        'security/ir.model.access.csv',
        'security/l10n_hr_evisitor_security.xml',
        'data/ir_sequence_data.xml',
        'data/ir_cron_data.xml',
        'views/res_company_views.xml',
        'views/l10n_hr_evisitor_accommodation_views.xml',
        'views/l10n_hr_evisitor_guest_registration_views.xml',
        'views/l10n_hr_evisitor_log_views.xml',
        'views/l10n_hr_evisitor_menu.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
    'countries': ['hr'],
}
