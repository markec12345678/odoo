# -*- coding: utf-8 -*-
{
    "name": "HR Accounting Base",
    "version": "19.0.1.0.0",
    "summary": "Croatian accounting foundation: partner OIB validation, "
    "company IBAN, payment model & reference, fiscal data setup. "
    "Base for all HR accounting modules.",
    "description": """
HR Accounting Base
==================

Foundation module for Croatian accounting localization. Provides:

1. **OIB validation** — Croatian Personal Identification Number (OIB)
   is 11 digits with ISO 7064 MOD 11-10 checksum. This module validates
   partner OIB on save and displays a warning if invalid.

2. **Payment model & reference** — Croatian payment system uses
   "model" (e.g. HR01) and "poziv na broj" (reference number) for
   bank transfers. Added on res.partner.bank and account.move.

3. **Fiscal data** — company fiscal position, MID (establishment ID),
   NKD code link, court registration number.

4. **Croatian invoice numbering** — supports the HR format
   (e.g. "RAC-2026-001/1") with location code prefix.

5. **Partner categories for HR** — domestic/foreign, VAT registered,
   related party (povezano lice).

This is the equivalent of OCA's `l10n_hr_account_base` (dajmi5).

Integrates with:
  * l10n_hr_nkd (activity codes)
  * account (invoice, tax, journal)
  * base_vat (VAT validation)
""",
    "author": "SI/HR Tourism Suite",
    "website": "https://github.com/markec12345678/odoo-si-hr-tourism-suite",
    "license": "LGPL-3",
    "category": "Accounting/Localizations/Croatia",
    "depends": ["account", "base_vat", "base_iban"],
    "external_dependencies": {
        "python": [],
    },
    "data": [
        "security/ir.model.access.csv",
        "views/res_partner_views.xml",
        "views/res_company_views.xml",
        "views/res_partner_bank_views.xml",
        "views/account_move_views.xml",
        "views/account_journal_views.xml",
        "views/hr_account_base_menus.xml",
    ],
    "installable": True,
    "application": False,
    "auto_install": False,
}
