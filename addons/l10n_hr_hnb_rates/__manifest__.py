# -*- coding: utf-8 -*-
{
    "name": "HR HNB Exchange Rates",
    "version": "19.0.1.0.0",
    "summary": "Auto-fetch daily exchange rates from Croatian National Bank "
    "(HNB) API. Updates currency.rate table automatically.",
    "description": """
HR HNB Exchange Rates
=====================

Automatically fetches daily exchange rates from the Croatian National Bank
(Hrvatska narodna banka — HNB) public API and updates Odoo's
`res.currency.rate` table.

HNB publishes daily rates for ~40 currencies against EUR (the official
Croatian currency since 1.1.2023).

Features:
- Daily cron at 09:00 fetches today's rates
- Manual fetch button on currency rate list
- Supports EUR base currency
- Stores rate date for audit
- Uses HNB official API: https://api.hnb.hr/tecajn/v2

Integrates with:
  * res.currency (standard Odoo currency model)
  * res.currency.rate (rate history)
  * account (automatic revaluation)
""",
    "author": "SI/HR Tourism Suite",
    "website": "https://github.com/markec12345678/odoo-si-hr-tourism-suite",
    "license": "LGPL-3",
    "category": "Accounting/Localizations/Croatia",
    "depends": ["base"],
    "external_dependencies": {
        "python": ["requests"],
    },
    "data": [
        "security/ir.model.access.csv",
        "data/ir_cron_data.xml",
        "views/hnb_rate_views.xml",
    ],
    "installable": True,
    "application": False,
    "auto_install": False,
}
