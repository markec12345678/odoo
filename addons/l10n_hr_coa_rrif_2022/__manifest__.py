# -*- coding: utf-8 -*-
{
    "name": "HR Chart of Accounts (RRIF 2022)",
    "version": "19.0.1.0.0",
    "summary": "Croatian RRIF 2022. chart of accounts, account groups, "
    "tax groups, fiscal positions, and tax templates. Based on RRIF "
    "official chart updated for EUR transition.",
    "description": """
HR Chart of Accounts (RRIF 2022)
================================

Provides the Croatian RRIF (Računovodstveni revizorski institut financija)
2022. chart of accounts — the most widely used chart in Croatia, updated
for the EUR currency transition (1.1.2023).

Includes:
- Account groups (5 levels: class → group → subgroup → account → subaccount)
- Account templates (~200 accounts covering all classes 0-9)
- Tax groups (PDV 25%, 13%, 5%, 0%, exempt)
- Tax templates with proper VAT accounts
- Fiscal positions (domestic, EU, foreign, reverse charge)
- Account tags for Croatian financial reports

Account classes (RRIF):
  0 — Assets (Aktiva)
  1 — Inventories (Zalihe)
  2 — Production costs (Troškovi proizvodnje)
  3 — Cost of goods sold (Troškovi nabave)
  4 — Operating expenses (Troškovi razdoblja)
  5 — Financial expenses (Financijski troškovi)
  6 — Revenues (Prihodi)
  7 — Other revenues (Ostali prihodi)
  8 — Financial revenues (Financijski prihodi)
  9 — Extraordinary items (Izvanredni prihodi i rashodi)

This is the equivalent of OCA's `l10n_hr_coa_rrif_2022` (dajmi5).
""",
    "author": "SI/HR Tourism Suite",
    "website": "https://github.com/markec12345678/odoo-si-hr-tourism-suite",
    "license": "LGPL-3",
    "category": "Accounting/Localizations/Account Charts",
    "depends": ["account", "l10n_hr"],
    "external_dependencies": {
        "python": [],
    },
    "data": [
        "security/ir.model.access.csv",
        "data/account.group.template.csv",
        "data/account.account.template.csv",
        "data/account.tax.group.csv",
        "data/account.tax.template.csv",
        "data/account.fiscal.position.csv",
        "data/account_chart_template_data.xml",
    ],
    "demo": [],
    "installable": True,
    "application": False,
    "auto_install": False,
}
