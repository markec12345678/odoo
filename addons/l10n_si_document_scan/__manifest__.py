# -*- coding: utf-8 -*-
{
    'name': 'SI Document Scanner — OCR for AJPES',
    'summary': 'Skeniranje osebnih dokumentov z AI OCR pred AJPES prijavo gostov',
    'version': '19.0.1.0.0',
    'category': 'Hospitality',
    'description': """
SI Document Scanner — OCR for AJPES
====================================

Skeniranje osebnih dokumentov (potni list, osebna izkaznica) z AI OCR
tehnologijo pred oddajo AJPES eTurizem prijave gostov.

Funkcionalnosti:
* Slikanje/fotografiranje osebnega dokumenta (potni list, OI)
* AI OCR preko AI Core (GLM 5.1 vision) ali Tesseract fallback
* Samodejno izpolnjevanje eTurism prijave (ime, priimek, datum rojstva,
  številka dokumenta, država, državljanstvo)
* Validacija podatkov (format številke dokumenta, datum rojstva)
* Povezava z l10n_si_etourism_guest_registration
* GDPR skladno — slike se ne shranjujejo trajno

Uporaba:
1. Recepcija poslika potni list/OI gosta
2. AI OCR prebere podatke
3. Sistem izpolni eTourism prijavo
4. Recepcija preveri in potrdi
5. Prijava se odda na AJPES

Podprti dokumenti:
* Slovenska osebna izkaznica (fizična + digitalna)
* Potni list (vsi države — ICAO 9303 MRZ format)
* Vozni list
* Druge osebne izkaznice (HR, EU)

Pravna podlaga:
* ZSPDOP (Zakon o varstvu osebnih podatov) — 5 let hrambe
* ZTUR-1 (Zakon o spodbujanju razvoja turizma) — 23. člen
* GDPR člen 6(1)(c) — zakonska obveznost
""",
    'author': 'markec12345678',
    'website': 'https://github.com/markec12345678/odoo-si-hr-tourism-suite',
    'license': 'LGPL-3',
    'depends': ['base', 'web', 'l10n_si_etourism'],
    'data': [
        'security/ir.model.access.csv',
        'views/l10n_si_document_scan_views.xml',
        'wizard/l10n_si_document_scan_wizard_views.xml',
    ],
    'installable': True,
    'auto_install': False,
}
