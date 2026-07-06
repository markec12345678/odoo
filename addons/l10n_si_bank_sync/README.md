# 🇸🇮 Slovenian Bank Sync

> Auto-fetch daily statements from NLB, NKBM, Sparkasse, Addiko

**Version**: 19.0.1.0.0 | **License**: LGPL-3 | **Countries**: si

## Dependencies

account, l10n_si, l10n_si_bank_parser

## Description

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
...

## Author

markec12345678 — [https://github.com/markec12345678/odoo](https://github.com/markec12345678/odoo)

---

Part of the [SI/HR Odoo 19 Localization](https://github.com/markec12345678/odoo) project.
