# -*- coding: utf-8 -*-
{
    'name': 'Slovenian Bank Sync',
    'summary': 'Auto-fetch daily statements from NLB, NKBM, Sparkasse, Addiko',
    'version': '19.0.1.0.0',
    'category': 'Accounting/Localizations',
    'description': """
Slovenian Bank Sync
====================

Automatically fetch daily bank statements from major Slovenian banks
and import them via `l10n_si_bank_parser`. Replaces Enterprise `bank_sync`.

Supported banks
---------------
| Bank | API | Auth |
|------|-----|------|
| NLB (Poslovni portal) | SOAP | cert + user |
| NKBM (e-Bank) | REST | cert |
| Sparkasse (George Business) | REST | OAuth2 |
| Addiko Bank | REST | API key |
| Raiffeisen | SOAP | cert |

Features
--------
* Per-bank configuration (credentials, account IBAN, journal)
* Daily cron job at 03:00 — pulls yesterday's statements
* Uses `l10n_si_bank_parser` for XML parsing
* Fallback to manual fetch button
* Audit log: every fetch recorded with success/error status
* Multi-currency support
* Idempotent: re-fetching same date won't create duplicates

Configuration
-------------
1. Accounting → Configuration → Journals → Bank → SI Bank Sync tab
2. Select bank, enter credentials
3. Test connection via "Test Connection" button
4. Enable auto-sync

References
----------
* NLB Poslovni portal API spec v2.1
* NKBM e-Bank REST API v1.5
* Sparkasse George Business API v3.0
""",
    'author': 'markec12345678',
    'website': 'https://github.com/markec12345678/odoo',
    'license': 'LGPL-3',
    'depends': [
        'account',
        'l10n_si',
        'l10n_si_bank_parser',
    ],
    'data': [
        'security/ir.model.access.csv',
        'data/ir_cron_data.xml',
        'views/l10n_si_bank_sync_config_views.xml',
        'views/l10n_si_bank_sync_log_views.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
    'countries': ['si'],
}
