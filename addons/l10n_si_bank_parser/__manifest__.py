# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    'name': 'Slovenian Bank Statement Parser',
    'summary': 'Import ISO 20022 CAMT.053 / MT940 statements from NLB, NKBM, Sparkasse, Addiko',
    'version': '19.0.1.0.1',
    'category': 'Accounting/Localizations',
    'description': """
Slovenian Bank Statement Parser
================================

Imports bank statements from major Slovenian banks:

| Bank | Format | Status |
|------|--------|--------|
| NLB (Nova Ljubljanska banka) | ISO 20022 CAMT.053 | ✅ |
| NKBM (Nova Kreditna banka Maribor) | ISO 20022 CAMT.053 | ✅ |
| Sparkasse (Hranilnica Ljubljanska) | ISO 20022 CAMT.053 | ✅ |
| Addiko Bank | ISO 20022 CAMT.053 | ✅ |
| Raiffeisen Bank | MT940 (legacy) | ✅ |
| A1 Banka | ISO 20022 CAMT.053 | ✅ |
| Hypo Banka (postaja H-Alpe-Adria) | ISO 20022 CAMT.053 | ✅ |

Features
--------
* Parse ISO 20022 CAMT.053 (XML) and MT940 (STA) formats
* Auto-create bank journal entries with proper debit/credit
* Auto-match payments to open invoices via:
    - Payment reference (model reference)
    - Partner VAT + amount
    - Partner name fuzzy match
* Multi-currency support (HRK, USD, GBP, but primary: EUR)
* Handles SI-specific quirks:
    - SKB-style double space in customer names
    - NLB prefix "PRILIV" / "ODLIV" in transaction codes
    - NKBM concatenated partner name field
* Reconciliation: leaves entries as "to reconcile" if no match

Configuration
-------------
1. Accounting → Configuration → Journals → Bank journal
2. Set "Bank Statement Format" to CAMT.053 or MT940
3. Import via Accounting → Bank → "Import Statement"
""",
    'author': 'markec12345678',
    'website': 'https://github.com/markec12345678/odoo',
    'license': 'LGPL-3',
    'depends': [
        'account',
        'l10n_si',
    ],
    'data': [
        'security/ir.model.access.csv',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
    'countries': ['si'],
}
