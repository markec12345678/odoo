# 🇸🇮 Slovenian VAT Number Validation

> Validate Slovenian VAT numbers (davčna številka) with MOD11 + FURS VIES check

**Version**: 19.0.1.0.0 | **License**: LGPL-3 | **Countries**: si

## Dependencies

base_vat, l10n_si

## Description

Slovenian VAT Number Validation
================================

Validates Slovenian VAT numbers (davčna številka) at two levels:

1. **Format validation (offline)** — verifies the 8-digit SI format and the
   MOD11 checksum used by FURS. Invalid numbers are rejected before save.
2. **Existence validation (online, optional)** — queries the FURS REST API
...

## Author

markec12345678 — [https://github.com/markec12345678/odoo](https://github.com/markec12345678/odoo)

---

Part of the [SI/HR Odoo 19 Localization](https://github.com/markec12345678/odoo) project.
