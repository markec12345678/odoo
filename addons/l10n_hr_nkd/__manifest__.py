# -*- coding: utf-8 -*-
{
    "name": "HR NKD Activity Codes",
    "version": "19.0.1.0.0",
    "summary": "Croatian NKD 2007. (national NACE) activity classification "
    "codes for partners and companies. Required for statistical reports.",
    "description": """
HR NKD Activity Codes
=====================

Provides the Croatian NKD 2007. (Nacionalna klasifikacija djelatnosti)
activity classification — the national version of EU NACE Rev. 2.

Used on:
  * res.partner (partner's primary activity)
  * res.company (company's registered activity)
  * Statistical reports to DZS
  * Tourist establishment registration

NKD structure (5 levels):
  - Section: A–U (21 letters)
  - Division: 2 digits (01–99)
  - Group: 3 digits
  - Class: 4 digits
  - Subclass: 5 digits (full NKD code)

Example: 55.10.1 = Hotels and similar accommodation (subclass)

This module:
1. Adds `nkd_code_id` on res.partner and res.company
2. Provides a searchable database of all NKD codes
3. Includes the most common tourism-related codes pre-loaded
""",
    "author": "SI/HR Tourism Suite",
    "website": "https://github.com/markec12345678/odoo-si-hr-tourism-suite",
    "license": "LGPL-3",
    "category": "Accounting/Localizations/Croatia",
    "depends": ["base"],
    "data": [
        "security/ir.model.access.csv",
        "data/nkd_code_data.xml",
        "views/nkd_code_views.xml",
        "views/res_partner_views.xml",
        "views/res_company_views.xml",
        "views/nkd_menus.xml",
    ],
    "installable": True,
    "application": False,
    "auto_install": False,
}
