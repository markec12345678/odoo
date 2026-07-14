# -*- coding: utf-8 -*-
{
    "name": "HR Banks Database",
    "version": "19.0.1.0.0",
    "summary": "Database of Croatian banks with SWIFT/BIC codes. "
    "Auto-fills bank info on res.partner.bank from IBAN.",
    "description": """
HR Banks Database
=================

Provides a database of Croatian banks with:
- Bank name (Croatian + English)
- SWIFT/BIC code
- Bank code (first 7 digits of HR IBAN — used by HUB3 QR)
- Active flag

When entering an IBAN on res.partner.bank, the system auto-detects the
bank (from the 7-digit bank code embedded in the IBAN) and fills in the
BIC and bank name.

Used by:
- res.partner.bank (auto-detect bank)
- HUB3 QR code generation (bank code lookup)
- Payment matching

Equivalent to OCA's `l10n_hr_bank` (dajmi5).
""",
    "author": "SI/HR Tourism Suite",
    "website": "https://github.com/markec12345678/odoo-si-hr-tourism-suite",
    "license": "LGPL-3",
    "category": "Accounting/Localizations/Croatia",
    "depends": ["base"],
    "data": [
        "security/ir.model.access.csv",
        "data/res_bank_data.xml",
        "views/res_bank_views.xml",
    ],
    "installable": True,
    "application": False,
    "auto_install": False,
}
