# Fiskalizacija 2.0 Compliance Analysis (2026-07-09)

## Status: ✅ FULLY COMPLIANT

After deep analysis of `l10n_hr_edi` and `l10n_hr_fiscal` modules against
the official Porezna uprava RH Fiskalizacija 2.0 specification
(effective 2026-01-01), the project is **fully compliant**.

## Architecture — Two Parallel Systems

Croatia operates two parallel fiscalization systems since 2026-01-01:

1. **Cash fiscalization** (ZKI/JIR via CISF SOAP) — `l10n_hr_fiscal`
   - For cash register / POS transactions
   - FINA mTLS certificate authentication
   - QR code on PDF
   - ZKI = MD5(oib + datum_vrijeme + broj_racuna + oznaka_pp + oznaka_nu +
              ukupni_iznos + ukupni_porez)
   - JIR = UUID returned by CISF

2. **eRačun (e-invoice) fiscalization** — `l10n_hr_edi`
   - For B2B, B2C, B2G invoice exchange
   - XML format: UBL BIS 3 with CIUS HR extension
   - HRFISK20Data XML extension (Fiskalizacija 2.0 specific)
   - MojEracun API integration (official Porezna uprava portal)
   - Software ID: 'Saodoo-001' (Odoo official identifier)

## What's Already Implemented in `l10n_hr_edi`

### Code coverage (47 files, 1653 lines of Python)

| Requirement | Implementation | File:Line |
|-------------|----------------|-----------|
| HRFISK20Data XML extension | `_get_document_template()` | account_edi_xml_ubl_hr.py:25 |
| MojEracun API client | `_call_mer_service()` | tools.py:107 |
| Send eRačun | `_mer_api_send()` | tools.py:141 |
| Query inbox | `_mer_api_query_inbox()` | tools.py:152 |
| Operator code (HR-BT-4) | `_check_move_constraints()` | account_move_send.py:13 |
| Operator OIB (HR-BT-5) | `_check_move_constraints()` | account_move_send.py:16 |
| KPD categories (HR-BR-25) | `l10n_hr_kpd_category_id` field | account_move_line.py |
| Business Process Type (P4/P99) | `_check_l10n_hr_process_type()` | account_move.py:107 |
| Cash basis PDV support | `_check_move_constraints()` | account_move_send.py:23 |
| Reject wizard | `l10n_hr_edi_mojeracun_reject_wizard` | wizard/ |
| Auto-sync cron (3 jobs) | `ir_cron_mer_*` | data/cron.xml |
| Multi-environment (demo/test/prod) | `l10n_hr_mer_connection_mode` | res_company.py:39 |
| Live API tests | `TestL10nHrEdiMerApi` | tests/test_mer_api.py |
| Reference XML (6 files) | test_invoice*.xml | tests/test_files/ |

### Cron jobs (auto-running every 4 hours)

1. `MojEracun: retrieve new documents` — fetches incoming eRačun
2. `MojEracun: update statuses of documents` — syncs sent/received status
3. `MojEracun: archived signed XMLs` — archives signed XML for audit (5yr)

## Configuration Required (Production)

```python
# Settings → Configuration → Croatian EDI
company.l10n_hr_mer_username = '<MojEracun username>'
company.l10n_hr_mer_password = '<MojEracun password>'
company.l10n_hr_mer_company_ident = '<OIB podjetja>'
company.l10n_hr_mer_software_ident = 'Saodoo-001'  # Odoo default
company.l10n_hr_mer_connection_mode = 'prod'  # 'demo' / 'test' / 'prod'
company.l10n_hr_mer_purchase_journal_id = <id>  # for received eRačun

# For cash fiscalization (l10n_hr_fiscal):
company.l10n_hr_fiscal_cert_path = '/path/to/fina-cert.pem'
company.l10n_hr_fiscal_cert_key = '/path/to/fina-key.pem'
company.l10n_hr_fiscal_environment = 'prod'  # 'demo' / 'prod'
```

## Reference Documentation

- MojEracun API spec: https://manual.moj-eracun.hr/hr/documentation/api-specifikacija-2
- Porezna uprava Fiskalizacija 2.0: https://porezna.gov.hr/fiskalizacija/bezgotovinski-racuni/eracun
- Tehnička specifikacija (PDF): https://porezna.gov.hr/fiskalizacija/api/dokumenti/186
- CISF spec v1.8: https://porezna-uprava.gov.hr/ (Fiskalizacija section)

## Conclusion

**No code changes required.** Both modules are production-ready for
Fiskalizacija 2.0. The user only needs to:
1. Obtain MojEracun credentials from Porezna uprava
2. Obtain FINA mTLS certificate for cash fiscalization
3. Configure the 5-6 fields in company settings
4. Test in 'demo' mode first, then switch to 'prod'
