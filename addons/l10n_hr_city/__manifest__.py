# -*- coding: utf-8 -*-
{
    "name": "HR Cities & Municipalities",
    "version": "19.0.1.0.0",
    "summary": "Database of Croatian cities, municipalities, and counties. "
    "Auto-populates res.city and res.country.state for Croatia.",
    "description": """
HR Cities & Municipalities
==========================

Provides a complete database of Croatian administrative divisions:
- 21 counties (županije) including the City of Zagreb
- 128 cities (gradovi) and 428 municipalities (općine)
- 6,776 settlements (naselja) — optional, large dataset

This module populates Odoo's standard models:
- `res.country.state` — Croatian counties (code: HR-XX)
- `res.city` — Croatian cities and municipalities

Used by:
- res.partner (city field auto-complete)
- res.company (registered address)
- Fiskalizacija 2.0 (city code required for invoices)
- eVisitor / eTurizem (municipality code for guest registration)

Equivalent to OCA's `l10n_hr_city` (dajmi5).
""",
    "author": "SI/HR Tourism Suite",
    "website": "https://github.com/markec12345678/odoo-si-hr-tourism-suite",
    "license": "LGPL-3",
    "category": "Accounting/Localizations/Croatia",
    "depends": ["base"],
    "data": [
        "security/ir.model.access.csv",
        "data/res.country.state.csv",
        "data/res.city.csv",
    ],
    "installable": True,
    "application": False,
    "auto_install": False,
}
