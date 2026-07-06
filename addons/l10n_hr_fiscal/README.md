# Croatian Fiscal Verification (Fiskalizacija 2.0) — l10n_hr_fiscal

**Odoo 19 module for Croatian cash invoice fiscalization per Zakon o fiskalizaciji**

## Status

**Phase 1 (data model + ZKI algorithm + SOAP client): COMPLETE ✅**

## ZKI Algorithm

Per CISF technical specification v1.8:

```
ZKI = MD5(oib + datum_vrijeme + broj_racuna + oznaka_pp + oznaka_nu + ukupni_iznos + ukupni_porez)
```

- `oib` — 11-digit Croatian OIB
- `datum_vrijeme` — `dd.MM.yyyyHH:mm:ss` (Croatian format)
- Date format differs from SI (ISO 8601)!

## CISF endpoints

- **DEMO:** `https://cistest.apis-it.hr:8449/FiskalizacijaServiceTest`
- **PROD:** `https://cis.porezna-uprava.gov.hr:8449/FiskalizacijaService`

Auth: FINA `.pfx` certificate with mTLS

## Configuration

1. Get FINA cert from https://cms.fina.hr (DEMO) or https://cms.fina.hr (PROD)
2. Settings → Companies → [company] → HR Fiskalizacija tab
3. Upload .pfx + password
4. Register business premises via CISF
5. Post invoice → ZKI/JIR auto-generated

## Legal

- Zakon o fiskalizaciji (NN 133/12, 145/14, 40/19)
- Penalty: 500–200.000 kn per unfiscalized invoice
