# Slovenian Localization Modules for Odoo 19.0

Six custom addons developed for the Slovenian market. All installed via the
standard `--addons-path` mechanism; each depends on the previous one(s) as
noted below.

## Modules

| Module | Depends on | Purpose |
|--------|-----------|---------|
| `l10n_si_vat_validation` | `base_vat`, `l10n_si` | MOD11 checksum + FURS VIES lookup for SI VAT numbers |
| `l10n_si_sequence` | `account`, `l10n_si` | Invoice numbering per poslovni prostor (BL1-KASA1-2025-00001) |
| `l10n_si_fiscal` | `l10n_si_sequence`, `l10n_si_vat_validation` | FURS davčno potrjevanje: ZOI, EOR, QR code, retry cron |
| `l10n_si_edi` | `account_edi_ubl_cii`, `l10n_si_vat_validation` | FURS e-Račun (eSLOG 2.0) generation, signing, submission |
| `l10n_si_bank_parser` | `account_bank_statement_import` | NLB/NKBM/Sparkasse/Addiko/Raiffeisen CAMT.053 + MT940 import |
| `l10n_si_reports` | `account`, `l10n_si_vat_validation` | AJPES SRS, REK-1, M4 XML exports for eDavki |

## Installation

```bash
# Already in the addons folder; just install from the Odoo Apps menu:
# Apps → Update Apps List → search for "Slovenian"

# Or via CLI:
./odoo-bin -d mydb -i l10n_si,l10n_si_vat_validation,l10n_si_sequence,l10n_si_fiscal,l10n_si_edi,l10n_si_bank_parser,l10n_si_reports --stop-after-init
```

## Configuration order

1. **`l10n_si_vat_validation`** — Company → SI VAT Validation tab → upload FURS .p12
2. **`l10n_si_sequence`** — Accounting → Configuration → Slovenian → Business Premises → register premise + devices
3. **`l10n_si_fiscal`** — Company → SI Fiscal Verification tab → enable + upload FURS cert + set environment
4. **`l10n_si_edi`** — Company → SI e-Račun tab → upload eIDAS cert + set PEPPOL ID
5. **`l10n_si_bank_parser`** — Accounting → Journals → Bank → set SI Bank Format
6. **`l10n_si_reports`** — Accounting → Reports → Slovenian Reports → generate per period

## Dependencies

Each module needs these additional Python packages on the server:

```bash
pip install qrcode requests xmlsec1
# xmlsec1 is a system package:
apt install xmlsec1  # Debian/Ubuntu
```

## Tests

Each module includes a tests/ directory. Run with:

```bash
./odoo-bin -d testdb -i l10n_si_vat_validation --test-enable --test-tags=/l10n_si_vat_validation --stop-after-init
```

## Legal

* **ZOI/EOR (l10n_si_fiscal)**: ZDavPR-1, UR. l. RS š. 89/16
* **e-Račun (l10n_si_edi)**: ZEfUP + EU Directive 2014/55/EU + EN 16931
* **REK-1 (l10n_si_reports)**: ZDDV-1, 81. člen
* **M4 (l10n_si_reports)**: ZDoh-2, 28. člen
* **AJPES SRS**: Pravilnik o vsebini in obliki računovodskih izkazov, UR. l. RS š. 60/06

## License

LGPL-3.0 — same as Odoo Community.
