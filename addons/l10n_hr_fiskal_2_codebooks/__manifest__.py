# -*- coding: utf-8 -*-
{
    "name": "HR Fiskalizacija 2.0 Codebooks",
    "version": "19.0.1.0.0",
    "summary": "UNTDID codebooks for Croatian Fiskalizacija 2.0: "
    "document types (1001), discount reasons (5189), tax categories "
    "(5305/5153). Required for eRačun B2B (PEPPOL EN16931).",
    "description": """
HR Fiskalizacija 2.0 Codebooks
==============================

Provides the three UNTDID codebooks mandated by Croatian Fiskalizacija 2.0
(obvezna od januarja 2026 za B2B e-invoicing):

1. **UNTDID 1001 — Document type** (l10n_hr.fiskal.document.type)
   - 380 Komerčni račun (Commercial invoice)
   - 381 Dobropis (Credit note)
   - 384 Korekcijski račun (Corrected invoice)
   - 389 Predračun (Proforma)
   - i dr.

2. **UNTDID 5189 — Discount reason** (l10n_hr.fiskal.discount.reason)
   - 100 Dogovoreni popust (Agreed discount)
   - 95 Gotovinski popust (Cash discount)
   - 62 Količinski popust (Volume discount)
   - i dr.

3. **UNTDID 5305/5153 — Tax category** (l10n_hr.fiskal.tax.category)
   - S Standardna stopa (Standard rate)
   - Z Nižja stopa (Lower rate)
   - E Davčno oproščeno (Exempt)
   - AE Reverse charge (Obrnjena davčna obveznost)
   - K Intra-community supply (Dobava znotraj EU)
   - G Izvoz (Export)
   - O Nična stopa (Zero rate)

Used by:
  * l10n_hr_edi (eRačun B2B XML generation)
  * l10n_hr_fiscal (Fiskalizacija 2.0 submission)
  * account.move ( invoice document type selection )
  * account.tax ( tax category mapping )

Sources:
  * https://porezna.gov.hr/fiskalizacija/
  * https://docs.peppol.eu/poacc/billing/3.0/codelist/
  * https://unece.org/trade/uncefact/cladelections (UNTDID)
""",
    "author": "SI/HR Tourism Suite",
    "website": "https://github.com/markec12345678/odoo-si-hr-tourism-suite",
    "license": "LGPL-3",
    "category": "Accounting/Localizations/Croatia",
    "depends": ["account"],
    "data": [
        "security/ir.model.access.csv",
        "data/document_type_data.xml",
        "data/discount_reason_data.xml",
        "data/tax_category_data.xml",
        "views/document_type_views.xml",
        "views/discount_reason_views.xml",
        "views/tax_category_views.xml",
        "views/account_tax_views.xml",
        "views/account_move_views.xml",
        "views/fiskal_codebook_menus.xml",
    ],
    "installable": True,
    "application": False,
    "auto_install": False,
}
